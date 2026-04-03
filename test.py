import sys
try:
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from ui.admin_dashboard import AdminDashboard
    win = AdminDashboard()
    print("FINISHED OK")
except Exception as e:
    import traceback
    with open("python_err.log", "w") as f:
        traceback.print_exc(file=f)
