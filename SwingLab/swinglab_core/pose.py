"""Stima della posa con MediaPipe Pose Landmarker (gira in locale, sulla CPU)."""
from __future__ import annotations

import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.signal import savgol_filter

from . import video as V

MODELLO_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
               "pose_landmarker_full/float16/latest/pose_landmarker_full.task")
MODELLO_PATH = Path(__file__).resolve().parent.parent / "models" / "pose_landmarker_full.task"


@dataclass
class Traccia:
    """Keypoint di un video: pixel (T,33,2), visibilità (T,33), mondo in metri (T,33,3)."""
    vista: str          # "A", "B" o "C"
    tipo: str           # "FO", "FO2", "DTL"
    fps: float
    larghezza: int
    altezza: int
    kp: np.ndarray
    vis: np.ndarray
    mondo: np.ndarray | None
    path: str | None = None
    frame_cache: dict = field(default_factory=dict)
    render: object = None   # per i dati sintetici: funzione indice → immagine

    @property
    def T(self):
        return self.kp.shape[0]

    def frame(self, i):
        if i in self.frame_cache:
            return self.frame_cache[i].copy()
        if self.render is not None:
            return self.render(i)
        if self.path:
            return V.leggi_frame(self.path, i)
        return None


def assicura_modello(progress=None) -> Path:
    """Scarica una volta il modello (~9 MB) nella cartella models/."""
    if MODELLO_PATH.exists() and MODELLO_PATH.stat().st_size > 1_000_000:
        return MODELLO_PATH
    MODELLO_PATH.parent.mkdir(parents=True, exist_ok=True)
    if progress:
        progress("Scarico il modello di posa (solo la prima volta)…")
    tmp = MODELLO_PATH.with_suffix(".tmp")
    urllib.request.urlretrieve(MODELLO_URL, tmp)
    tmp.replace(MODELLO_PATH)
    return MODELLO_PATH


def stima_posa(path: str, vista: str, tipo: str, fps: float, progress=None) -> Traccia:
    import mediapipe as mp
    from mediapipe.tasks import python as mpp
    from mediapipe.tasks.python import vision

    modello = assicura_modello(progress)
    opzioni = vision.PoseLandmarkerOptions(
        base_options=mpp.BaseOptions(model_asset_path=str(modello)),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    info = V.info_video(path, fps)
    n, w, h = info["frames"], info["larghezza"], info["altezza"]
    kp = np.full((n, 33, 2), np.nan)
    vis = np.zeros((n, 33))
    mondo = np.full((n, 33, 3), np.nan)
    # I timestamp devono crescere: usiamo il tempo reale dello swing.
    passo_ms = 1000.0 / fps
    with vision.PoseLandmarker.create_from_options(opzioni) as det:
        for i, rgb, _ in V.itera_frame(path):
            if i >= n:
                break
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
            res = det.detect_for_video(img, int(round(i * passo_ms)))
            if res.pose_landmarks:
                lm = res.pose_landmarks[0]
                kp[i] = [[p.x * w, p.y * h] for p in lm]
                vis[i] = [getattr(p, "visibility", 1.0) or 0.0 for p in lm]
                if res.pose_world_landmarks:
                    mondo[i] = [[p.x, p.y, p.z] for p in res.pose_world_landmarks[0]]
            if progress and i % 15 == 0:
                progress(f"Vista {vista}: fotogramma {i + 1}/{n}", (i + 1) / n)
    if np.isnan(kp[:, 0, 0]).mean() > 0.5:
        raise RuntimeError(f"Vista {vista}: golfer non rilevato nella maggior parte "
                           "dei fotogrammi. Controlla inquadratura e luce.")
    return Traccia(vista, tipo, fps, w, h, pulisci(kp, fps), vis, pulisci(mondo, fps), path)


def pulisci(arr: np.ndarray, fps: float) -> np.ndarray:
    """Riempie i buchi per interpolazione e leviga con Savitzky-Golay."""
    a = arr.copy()
    T = a.shape[0]
    t = np.arange(T)
    flat = a.reshape(T, -1)
    for j in range(flat.shape[1]):
        col = flat[:, j]
        ok = ~np.isnan(col)
        if ok.sum() >= 2:
            flat[:, j] = np.interp(t, t[ok], col[ok])
    # finestra ≈ 50 ms: abbastanza corta da non appiattire l'impatto
    win = max(5, int(round(fps * 0.05)) | 1)
    if T > win + 2:
        flat = savgol_filter(flat, win, 2, axis=0)
    return flat.reshape(a.shape)
