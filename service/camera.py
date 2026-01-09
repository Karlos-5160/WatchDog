import cv2
import time
import os

def capture_intruder_file(save_dir, cam_index=0):
    """
    Captures a single frame and saves it to the specified directory.
    Returns the absolute path of the saved file, or None if failed.
    Optimized for speed (no warmup).
    """
    try:
        cam = cv2.VideoCapture(cam_index)
        
        # Immediate read, no warmup (optimized)
        ret, frame = cam.read()
        
        if not ret:
            # Quick retry
            time.sleep(0.1)
            ret, frame = cam.read()

        cam.release()
        
        if ret:
            timestamp = int(time.time())
            filename = f"capture_{timestamp}.jpg"
            save_path = os.path.join(save_dir, filename)
            cv2.imwrite(save_path, frame)
            return save_path
            
    except Exception as e:
        print(f"[ERROR] Camera capture failed: {e}")
        
    return None
