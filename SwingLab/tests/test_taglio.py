"""Controlli del taglio video (durata e inquadratura)."""
import os
import sys
import tempfile

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swinglab_core import taglio  # noqa: E402


def _video(path, secondi=4, fps=60, w=320, h=480):
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for i in range(int(secondi * fps)):
        f = np.full((h, w, 3), i % 255, np.uint8)
        out.write(f)
    out.release()


def test_taglio_durata_e_inquadratura():
    d = tempfile.mkdtemp()
    src, dst = os.path.join(d, "a.mp4"), os.path.join(d, "b.mp4")
    _video(src)
    r = taglio.applica(src, dst, 1.0, 2.5, (0.25, 0.75, 0.1, 0.9))
    i = taglio.info(dst)
    assert abs(i["fps"] - 60) < 0.5                      # frame rate invariato
    assert abs(i["durata"] - 1.5) < 0.05
    assert (i["larghezza"], i["altezza"]) == (160, 384) == (r["larghezza"], r["altezza"])
    assert os.path.getsize(dst) < os.path.getsize(src)


def test_anteprima_e_intero():
    d = tempfile.mkdtemp()
    src = os.path.join(d, "a.mp4")
    _video(src)
    img = taglio.anteprima(src, 2.0, (0.1, 0.9, 0, 1), 200)
    assert img.shape[1] == 200
    assert taglio.intero(0, 4.0, 4.0, (0, 1, 0, 1)) and not taglio.intero(0.5, 4.0, 4.0, (0, 1, 0, 1))


if __name__ == "__main__":
    test = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in test:
        t()
        print("OK ", t.__name__)
    print(f"\nTutti i {len(test)} test superati.")
