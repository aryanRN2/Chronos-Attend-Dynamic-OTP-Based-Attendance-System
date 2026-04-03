# Chronos-Attend-Dynamic-OTP-Based-Attendance-System(antigravity)

This is a simple web app I built to make classroom attendance a bit more modern. Instead of doing roll calls, the teacher generates a temporary OTP on their screen, and students enter it on their own devices to get marked present.

How it works
Teachers: Log in and hit a button to generate a 6-digit OTP. The code automatically expires after 5 minutes, which stops students from just texting the code to friends who aren't actually in class.

Students: Log in to their dashboard, type the OTP they see on the board into the form. If it's the right code and they enter it in time, their attendance is saved!

Tech Stack
Backend: Python & Flask

Database: Flask-SQLAlchemy (using SQLite for local testing, but easy to migrate to PostgreSQL)

Frontend: HTML, CSS, and Jinja2 templates

A quick note on Antigravity
I used the Antigravity AI to help scaffold this project. I fed it my database requirements and logic rules, and it helped write out the boilerplate Flask code, SQLAlchemy models, and the initial Jinja templates. It essentially acted as my pair-programmer, saving me a ton of time on repetitive typing so I could focus on how the app actually works.

How to run it locally
If you want to spin this up on your own machine, follow these steps:

Clone this repository.

Create and activate a virtual environment.

Install the dependencies:

Bash
pip install -r requirements.txt
Initialize the database and run the app:

Bash
python app.py
Open your browser and go to http://127.0.0.1:5000
