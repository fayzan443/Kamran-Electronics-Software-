import sys
import os

# Path setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("Initializing System...")
    
    try:
        # Check requirements before proceeding
        import PyQt6
        import mysql.connector
        import pandas
        import matplotlib
        
        from database.db_handler import connect_server, create_tables
        from ui.db_setup_dialog import DBSetupDialog
        
        db_ok = False
        try:
            conn = connect_server()
            conn.close()
            db_ok = True
            print("Database connection verified.")
        except Exception:
            pass
            
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        
        if not db_ok:
            setup = DBSetupDialog()
            if setup.exec() == 0: 
                return
            
        create_tables()
            
        from ui.main_window import MainWindow
        window = MainWindow() 
        window.show()
        
        try:
            window.load_initial_data()
        except:
            pass
            
        print("Application is running.")
        sys.exit(app.exec())

    except ImportError as e:
        print(f"\n[CRITICAL ERROR] Missing Dependencies!")
        print(f"Details: {e}")
        print("\nPlease run: pip install -r requirements.txt")
        input("\nPress Enter to close...")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nAn error occurred: {e}")
        input("\nPress Enter to close...")


if __name__ == "__main__":
    main()