# Teacher Attendance Portal

A professional Flask-based web application for teachers to manage student attendance, track eligibility, and send WhatsApp notifications to parents when attendance falls below 75%.

## Features

- 📊 **Professional Dashboard** - View comprehensive attendance statistics and student details
- 📤 **File Upload** - Easy Excel file upload interface for updating attendance data
- ✅ **Automatic Eligibility** - Automatic status calculation (Eligible/Not Eligible based on 75% threshold)
- 📱 **WhatsApp Integration** - One-click WhatsApp notifications to parents
- 📈 **Real-time Statistics** - View total students, eligible count, and students needing attention
- 🎨 **Modern UI** - Professional, responsive design with intuitive navigation
- 🔒 **Data Validation** - File validation ensures data integrity

## Requirements

- Python 3.7+
- Flask
- Pandas
- OpenPyXL

## Installation

1. Clone or download this repository

2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Setup

1. **Database Setup**: The application uses an Excel file (`database/attendance.xlsx`) with the following columns:
   - `Name`: Student name
   - `Attended`: Number of classes attended
   - `Total Classes`: Total number of classes
   - `ParentMobile`: Parent's mobile number (10 digits, without country code)

2. **Sample Data**: A sample Excel file with test data is already included in the `database` folder.

## Usage

1. Run the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. **Upload Attendance Data**:
   - Click on "Upload" in the navigation bar
   - Select an Excel file (.xlsx or .xls) with the required columns
   - Click "Upload File" to update the database

4. **View Dashboard**:
   - See statistics: Total students, Eligible count, Students needing attention
   - View detailed attendance table with:
     - Student names
     - Attendance percentages with visual progress bars
     - Eligibility status badges
     - WhatsApp notification links (for students below 75% attendance)

## Project Structure

```
attendance_project/
├── app.py                 # Main Flask application with upload functionality
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .gitignore            # Git ignore file
├── templates/            # Flask templates (standard structure)
│   ├── index.html        # Dashboard template
│   └── upload.html       # File upload page
├── static/               # Flask static files (standard structure)
│   └── css/
│       └── style.css     # Professional styling
├── database/
│   └── attendance.xlsx   # Student attendance data
└── uploads/              # Temporary file upload directory
```

## Customization

### Changing Attendance Threshold

To change the minimum attendance percentage threshold, edit `app.py`:

```python
df["Status"] = df["Percentage"].apply(
    lambda x: "Eligible" if x >= 75 else "Not Eligible"  # Change 75 to your desired threshold
)
```

### Updating Student Data

**Option 1: Using the Web Interface (Recommended)**
- Navigate to the "Upload" page
- Select your Excel file and upload it
- The system will validate and update the database automatically

**Option 2: Manual Update**
- Edit the `database/attendance.xlsx` file directly
- Make sure to maintain the column structure:
  - Name
  - Attended
  - Total Classes
  - ParentMobile

## Notes

- The WhatsApp link format assumes Indian phone numbers (country code 91)
- Mobile numbers should be 10 digits without the country code
- The application runs in debug mode by default (change `debug=True` to `debug=False` in production)

## License

This project is open source and available for educational purposes.

