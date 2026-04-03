import sys
import traceback
import subprocess

def check_dependencies():
    print("========================================")
    print(" FACE RECOGNITION DEPENDENCY CHECKER")
    print("========================================")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version.split(' ')[0]}")
    print("----------------------------------------")
    
    dependencies = [
        ("numpy", "numpy"),
        ("cv2", "cv2"),
        ("dlib", "dlib"),
        ("face_recognition", "face_recognition")
    ]
    
    all_good = True
    for module_name, import_name in dependencies:
        try:
            mod = __import__(import_name)
            version = getattr(mod, '__version__', 'unknown')
            print(f"  [OK]   {module_name:<20} (version: {version})")
        except ImportError as e:
            print(f"  [FAIL] {module_name:<20} - Error: {e}")
            all_good = False
            
    print("----------------------------------------")
    if all_good:
        print("[SUCCESS] All face recognition dependencies are successfully installed!")
        print("\nNote: If you are still seeing the dependency error in your application,")
        print("it is likely because your Django development server needs to be restarted")
        print("after installing the dependencies.")
        print("Please stop your running `manage.py runserver` commands and start them again.")
    else:
        print("[ERROR] Some dependencies are missing or failing to import.")
        print("Please investigate the import errors above and install missing packages.")

if __name__ == "__main__":
    check_dependencies()
