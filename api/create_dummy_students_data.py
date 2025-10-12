#!/usr/bin/env python3
"""
Script to create a dummy students table with 10 records for testing SQL generation.
"""

import random
import json
import os
from dotenv import load_dotenv
from database.postgres_connection import get_db_connection

# Load environment variables
load_dotenv()

# Student data templates
FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", 
    "Ivy", "Jack", "Kate", "Liam", "Maya", "Noah", "Olivia", "Paul", 
    "Quinn", "Ruby", "Sam", "Tara", "Uma", "Victor", "Wendy", "Xavier", "Yara", "Zoe"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
]

MAJORS = [
    "Computer Science", "Mathematics", "Physics", "Chemistry", "Biology", 
    "Engineering", "Business", "Economics", "Psychology", "History", 
    "Literature", "Art", "Music", "Medicine", "Law", "Education"
]

GRADES = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"]

def generate_student_data():
    """Generate a single student record with realistic data."""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    # Generate realistic age (18-25)
    age = random.randint(18, 25)
    
    # Generate realistic GPA (1.0-4.0)
    gpa = round(random.uniform(1.0, 4.0), 2)
    
    # Generate realistic grade
    grade = random.choice(GRADES)
    
    # Generate major
    major = random.choice(MAJORS)
    
    return {
        "id": None,  # Will be auto-generated
        "first_name": first_name,
        "last_name": last_name,
        "age": age,
        "gpa": gpa,
        "grade": grade,
        "major": major
    }

def create_students_table():
    """Create the students table with proper schema."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        age INTEGER NOT NULL,
        gpa DECIMAL(3,2) NOT NULL,
        grade VARCHAR(5) NOT NULL,
        major VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_students_major ON students(major);
    CREATE INDEX IF NOT EXISTS idx_students_gpa ON students(gpa);
    CREATE INDEX IF NOT EXISTS idx_students_grade ON students(grade);
    """
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(create_table_sql)
            conn.commit()
            print("Students table created successfully")

def insert_students_data(num_students=10):
    """Insert dummy student data into the students table."""
    print(f"Generating {num_students} student records...")
    
    students_data = []
    for i in range(num_students):
        student = generate_student_data()
        students_data.append(student)
    
    # Prepare insert statement
    insert_sql = """
    INSERT INTO students (first_name, last_name, age, gpa, grade, major)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Clear existing data
            cursor.execute("DELETE FROM students")
            print("Cleared existing students data")
            
            # Insert new data
            for student in students_data:
                cursor.execute(insert_sql, (
                    student["first_name"], 
                    student["last_name"], 
                    student["age"], 
                    student["gpa"], 
                    student["grade"], 
                    student["major"]
                ))
            
            conn.commit()
            print(f"Successfully inserted {len(students_data)} student records")

def verify_data():
    """Verify the inserted data."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Count total records
            cursor.execute("SELECT COUNT(*) FROM students")
            count = cursor.fetchone()[0]
            print(f"Total students in database: {count}")
            
            # Show some sample data
            cursor.execute("SELECT first_name, last_name, age, gpa, grade, major FROM students LIMIT 5")
            samples = cursor.fetchall()
            print("\nSample records:")
            for sample in samples:
                print(f"  {sample[0]} {sample[1]} - Age: {sample[2]}, GPA: {sample[3]}, Grade: {sample[4]}, Major: {sample[5]}")
            
            # Show statistics
            cursor.execute("SELECT major, COUNT(*) as count FROM students GROUP BY major ORDER BY count DESC")
            majors = cursor.fetchall()
            print("\nMajors distribution:")
            for major, count in majors:
                print(f"  {major}: {count}")
            
            cursor.execute("SELECT MIN(gpa), MAX(gpa), AVG(gpa) FROM students")
            gpa_stats = cursor.fetchone()
            print(f"\nGPA range: {gpa_stats[0]} - {gpa_stats[1]} (avg: {gpa_stats[2]:.2f})")
            
            cursor.execute("SELECT MIN(age), MAX(age) FROM students")
            age_range = cursor.fetchone()
            print(f"Age range: {age_range[0]} - {age_range[1]}")

if __name__ == "__main__":
    print("Creating dummy students database...")
    
    try:
        # Create table
        create_students_table()
        
        # Insert data
        insert_students_data(10)
        
        # Verify data
        verify_data()
        
        print("\nDummy students database created successfully!")
        print("\nYou can now test SQL generation with queries like:")
        print("- 'Show me all computer science students'")
        print("- 'Find students with GPA above 3.5'")
        print("- 'List all students by major'")
        print("- 'Show me students with A grades'")
        print("- 'Find students older than 20'")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
