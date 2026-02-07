from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import pandas as pd
import urllib.parse
import os

# Get the base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Standard Flask structure - templates/ and static/ folders at root
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['DATABASE_FOLDER'] = os.path.join(BASE_DIR, 'database')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# Ensure upload and database directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATABASE_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_excel_path():
    """Get the path to the attendance Excel file"""
    return os.path.join(app.config['DATABASE_FOLDER'], "attendance.xlsx")

def load_dataframe():
    """Load the attendance dataframe from Excel"""
    excel_path = get_excel_path()
    if not os.path.exists(excel_path):
        # Create empty dataframe with required columns
        return pd.DataFrame(columns=['Name', 'Attended', 'Total Classes', 'ParentMobile'])
    return pd.read_excel(excel_path)

def save_dataframe(df):
    """Save the dataframe to Excel file"""
    excel_path = get_excel_path()
    df.to_excel(excel_path, index=False)

@app.route("/")
def index():
    try:
        df = load_dataframe()
        
        if df.empty:
            return render_template("index.html", students=[], error="No attendance data found. Please add students or upload an Excel file.")
        
        # Calculate percentage and handle division by zero
        df["Percentage"] = df.apply(
            lambda row: (row["Attended"] / row["Total Classes"] * 100) if row["Total Classes"] > 0 else 0,
            axis=1
        )
        df["Status"] = df["Percentage"].apply(
            lambda x: "Eligible" if x >= 75 else "Not Eligible"
        )

        students = []
        total_students = len(df)
        eligible_count = len(df[df["Percentage"] >= 75])
        not_eligible_count = total_students - eligible_count

        for idx, row in df.iterrows():
            try:
                percentage = round(row['Percentage'], 2)
                status = row['Status']
                
                # Custom message for defaulters
                if status == "Not Eligible":
                    message = f"""Dear Parent/Guardian,

Your child *{row['Name']}* attendance is *{percentage}%* which is *less than the required 75%*.

*Attendance Details:*
• Classes Attended: {int(row['Attended'])}
• Total Classes: {int(row['Total Classes'])}
• Current Attendance: {percentage}%

*Action Required:*
Please ensure your child attends classes regularly to maintain the minimum 75% attendance requirement.

Thank you for your cooperation."""
                else:
                    message = f"""Dear Parent/Guardian,

Your child *{row['Name']}* attendance is *{percentage}%* which meets the required standard.

*Attendance Details:*
• Classes Attended: {int(row['Attended'])}
• Total Classes: {int(row['Total Classes'])}
• Current Attendance: {percentage}%

Keep up the good attendance!

Thank you."""
                
                encoded_msg = urllib.parse.quote(message)
                whatsapp_link = f"https://wa.me/91{int(row['ParentMobile'])}?text={encoded_msg}"

                students.append({
                    "id": int(idx),
                    "name": row["Name"],
                    "attended": int(row["Attended"]),
                    "total_classes": int(row["Total Classes"]),
                    "parent_mobile": str(int(row["ParentMobile"])),
                    "percentage": round(row["Percentage"], 2),
                    "status": row["Status"],
                    "whatsapp": whatsapp_link
                })
            except (ValueError, KeyError) as e:
                # Skip rows with invalid data
                continue

        return render_template("index.html", students=students, 
                             total_students=total_students,
                             eligible_count=eligible_count,
                             not_eligible_count=not_eligible_count)
    
    except Exception as e:
        return render_template("index.html", students=[], error=f"Error loading data: {str(e)}")

@app.route("/upload", methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected. Please choose an Excel file.', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            flash('No file selected. Please choose an Excel file.', 'error')
            return redirect(request.url)
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload an Excel file (.xlsx or .xls).', 'error')
            return redirect(request.url)
        
        try:
            # Save uploaded file temporarily
            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)
            
            # Validate Excel file structure
            df = pd.read_excel(temp_path)
            required_columns = ['Name', 'Attended', 'Total Classes', 'ParentMobile']
            
            if not all(col in df.columns for col in required_columns):
                os.remove(temp_path)
                flash(f'Invalid file format. Excel file must contain columns: {", ".join(required_columns)}', 'error')
                return redirect(request.url)
            
            # Validate data types
            try:
                df['Attended'] = pd.to_numeric(df['Attended'], errors='coerce')
                df['Total Classes'] = pd.to_numeric(df['Total Classes'], errors='coerce')
                df['ParentMobile'] = pd.to_numeric(df['ParentMobile'], errors='coerce')
            except Exception:
                os.remove(temp_path)
                flash('Invalid data types in Excel file. Please check your data.', 'error')
                return redirect(request.url)
            
            # Save to database
            save_dataframe(df)
            
            # Remove temporary file
            os.remove(temp_path)
            
            flash(f'File uploaded successfully! {len(df)} student records loaded.', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template("upload.html")

@app.route("/students", methods=['GET'])
def manage_students():
    """Display all students for management"""
    try:
        df = load_dataframe()
        
        if df.empty:
            return render_template("manage_students.html", students=[])
        
        students = []
        for idx, row in df.iterrows():
            try:
                percentage = (row["Attended"] / row["Total Classes"] * 100) if row["Total Classes"] > 0 else 0
                status = "Eligible" if percentage >= 75 else "Not Eligible"
                
                students.append({
                    "id": int(idx),
                    "name": row["Name"],
                    "attended": int(row["Attended"]),
                    "total_classes": int(row["Total Classes"]),
                    "parent_mobile": str(int(row["ParentMobile"])),
                    "percentage": round(percentage, 2),
                    "status": status
                })
            except (ValueError, KeyError):
                continue
        
        return render_template("manage_students.html", students=students)
    except Exception as e:
        flash(f'Error loading students: {str(e)}', 'error')
        return render_template("manage_students.html", students=[])

@app.route("/students/add", methods=['GET', 'POST'])
def add_student():
    """Add a new student"""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            attended = request.form.get('attended', '0')
            total_classes = request.form.get('total_classes', '0')
            parent_mobile = request.form.get('parent_mobile', '').strip()
            
            # Validation
            if not name:
                flash('Student name is required.', 'error')
                return redirect(url_for('add_student'))
            
            if not parent_mobile or not parent_mobile.isdigit() or len(parent_mobile) != 10:
                flash('Parent mobile number must be exactly 10 digits.', 'error')
                return redirect(url_for('add_student'))
            
            try:
                attended = int(attended)
                total_classes = int(total_classes)
                if attended < 0 or total_classes < 0:
                    raise ValueError("Negative values not allowed")
                if attended > total_classes:
                    flash('Attended classes cannot be greater than total classes.', 'error')
                    return redirect(url_for('add_student'))
            except ValueError:
                flash('Attended and Total Classes must be valid positive numbers.', 'error')
                return redirect(url_for('add_student'))
            
            # Load existing data
            df = load_dataframe()
            
            # Add new student
            new_row = pd.DataFrame({
                'Name': [name],
                'Attended': [attended],
                'Total Classes': [total_classes],
                'ParentMobile': [int(parent_mobile)]
            })
            df = pd.concat([df, new_row], ignore_index=True)
            
            # Save to Excel
            save_dataframe(df)
            
            flash(f'Student "{name}" added successfully!', 'success')
            return redirect(url_for('manage_students'))
            
        except Exception as e:
            flash(f'Error adding student: {str(e)}', 'error')
            return redirect(url_for('add_student'))
    
    return render_template("add_student.html")

@app.route("/students/edit/<int:student_id>", methods=['GET', 'POST'])
def edit_student(student_id):
    """Edit an existing student"""
    try:
        df = load_dataframe()
        
        if student_id < 0 or student_id >= len(df):
            flash('Student not found.', 'error')
            return redirect(url_for('manage_students'))
        
        if request.method == 'POST':
            try:
                name = request.form.get('name', '').strip()
                attended = request.form.get('attended', '0')
                total_classes = request.form.get('total_classes', '0')
                parent_mobile = request.form.get('parent_mobile', '').strip()
                
                # Validation
                if not name:
                    flash('Student name is required.', 'error')
                    return redirect(url_for('edit_student', student_id=student_id))
                
                if not parent_mobile or not parent_mobile.isdigit() or len(parent_mobile) != 10:
                    flash('Parent mobile number must be exactly 10 digits.', 'error')
                    return redirect(url_for('edit_student', student_id=student_id))
                
                try:
                    attended = int(attended)
                    total_classes = int(total_classes)
                    if attended < 0 or total_classes < 0:
                        raise ValueError("Negative values not allowed")
                    if attended > total_classes:
                        flash('Attended classes cannot be greater than total classes.', 'error')
                        return redirect(url_for('edit_student', student_id=student_id))
                except ValueError:
                    flash('Attended and Total Classes must be valid positive numbers.', 'error')
                    return redirect(url_for('edit_student', student_id=student_id))
                
                # Update student data
                df.at[student_id, 'Name'] = name
                df.at[student_id, 'Attended'] = attended
                df.at[student_id, 'Total Classes'] = total_classes
                df.at[student_id, 'ParentMobile'] = int(parent_mobile)
                
                # Save to Excel
                save_dataframe(df)
                
                flash(f'Student "{name}" updated successfully!', 'success')
                return redirect(url_for('manage_students'))
                
            except Exception as e:
                flash(f'Error updating student: {str(e)}', 'error')
                return redirect(url_for('edit_student', student_id=student_id))
        
        # GET request - show edit form
        student = df.iloc[student_id]
        student_data = {
            "id": student_id,
            "name": student["Name"],
            "attended": int(student["Attended"]),
            "total_classes": int(student["Total Classes"]),
            "parent_mobile": str(int(student["ParentMobile"]))
        }
        
        return render_template("edit_student.html", student=student_data)
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('manage_students'))

@app.route("/students/delete/<int:student_id>", methods=['POST'])
def delete_student(student_id):
    """Delete a student"""
    try:
        df = load_dataframe()
        
        if student_id < 0 or student_id >= len(df):
            flash('Student not found.', 'error')
            return redirect(url_for('manage_students'))
        
        student_name = df.iloc[student_id]['Name']
        
        # Remove student
        df = df.drop(df.index[student_id]).reset_index(drop=True)
        
        # Save to Excel
        save_dataframe(df)
        
        flash(f'Student "{student_name}" deleted successfully!', 'success')
        return redirect(url_for('manage_students'))
        
    except Exception as e:
        flash(f'Error deleting student: {str(e)}', 'error')
        return redirect(url_for('manage_students'))

@app.route("/students/notify/<int:student_id>", methods=['GET'])
def notify_parent(student_id):
    """Send WhatsApp notification to parent"""
    try:
        df = load_dataframe()
        
        if student_id < 0 or student_id >= len(df):
            flash('Student not found.', 'error')
            return redirect(url_for('index'))
        
        student = df.iloc[student_id]
        percentage = round((student["Attended"] / student["Total Classes"] * 100) if student["Total Classes"] > 0 else 0, 2)
        status = "Eligible" if percentage >= 75 else "Not Eligible"
        
        # Custom message for defaulters
        if status == "Not Eligible":
            message = f"""Dear Parent/Guardian,

Your child *{student['Name']}* attendance is *{percentage}%* which is *less than the required 75%*.

*Attendance Details:*
• Classes Attended: {int(student['Attended'])}
• Total Classes: {int(student['Total Classes'])}
• Current Attendance: {percentage}%

*Action Required:*
Please ensure your child attends classes regularly to maintain the minimum 75% attendance requirement.

Thank you for your cooperation."""
        else:
            message = f"""Dear Parent/Guardian,

Your child *{student['Name']}* attendance is *{percentage}%* which meets the required standard.

*Attendance Details:*
• Classes Attended: {int(student['Attended'])}
• Total Classes: {int(student['Total Classes'])}
• Current Attendance: {percentage}%

Keep up the good attendance!

Thank you."""
        
        encoded_msg = urllib.parse.quote(message)
        whatsapp_link = f"https://wa.me/91{int(student['ParentMobile'])}?text={encoded_msg}"
        
        return redirect(whatsapp_link)
        
    except Exception as e:
        flash(f'Error generating notification: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
