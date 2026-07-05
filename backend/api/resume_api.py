from flask import Blueprint, request, jsonify
from modules.resume_parsing.pdf_reader import extract_text_from_pdf
from modules.resume_parsing.text_preprocessor import preprocess_for_structure, preprocess_for_nlp
from modules.resume_parsing.experience_extractor import extract_experience_blocks
from modules.resume_parsing.skill_extractor import extract_skills
from modules.resume_parsing.skill_experience_mapper import map_skill_experience
from modules.resume_parsing.experience_classifier import classify_experience
from modules.resume_parsing.skill_categorizer import categorize_skills
from modules.resume_parsing.resume_validator import validate_resume
from modules.resume_parsing.summary_generator import generate_professional_summary
from config.db_config import get_db_connection

resume_api = Blueprint('resume_api', __name__)

@resume_api.route('/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        try:
            # Pass the file stream directly to the pdf_reader
            raw_text = extract_text_from_pdf(file.stream)
            
            if raw_text:
                # Validate that the extracted text resembles a real resume
                is_valid, validation_msg = validate_resume(raw_text)
                if not is_valid:
                    return jsonify({'success': False, 'message': validation_msg}), 400

                # Preprocess the text
                structured_text = preprocess_for_structure(raw_text)
                nlp_text = preprocess_for_nlp(raw_text)

                # Extract Experience Blocks (Temporary Object)
                experience_blocks = extract_experience_blocks(structured_text)

                # Extract Skills (Rule-based from DB)
                extracted_skills = extract_skills(nlp_text)

                # Calculate Total Experience
                total_experience = round(sum(b.get('duration', 0) for b in experience_blocks), 1)

                # Map Skills to Experience Durations
                skill_experience = map_skill_experience(experience_blocks, extracted_skills, total_experience)

                # Get database connection and cursor
                conn = get_db_connection()
                cursor = conn.cursor()

                # Get user name for summary
                cursor.execute("SELECT full_name FROM users WHERE id = %s", (user_id,))
                user_row = cursor.fetchone()
                full_name = user_row[0] if user_row else "Professional"

                # Categorize Skills
                categorized_skills = categorize_skills(skill_experience)

                # Generate Professional Summary
                prof_summary = generate_professional_summary(full_name, total_experience, extracted_skills)

                # Store extracted text and total experience in the database
                query = """
                    INSERT INTO resumes (user_id, extracted_text, processed_text_nlp, total_experience) 
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        extracted_text = %s,
                        processed_text_nlp = %s,
                        total_experience = %s
                """
                cursor.execute(query, (user_id, structured_text, nlp_text, total_experience, structured_text, nlp_text, total_experience))

                # Clear old skills to ensure synchronization with the latest resume
                cursor.execute("DELETE FROM user_skills WHERE user_id = %s", (user_id,))

                # Store skills and their experience levels in user_skills table
                for skill_name, years in skill_experience.items():
                    # 1. Get skill_id for the standardized skill name
                    cursor.execute("SELECT id FROM skills WHERE skill_name = %s", (skill_name,))
                    skill_row = cursor.fetchone()
                    
                    if skill_row:
                        skill_id = skill_row[0]
                        exp_level = classify_experience(years)
                        
                        # 2. Insert new user_skills record
                        skill_query = """
                            INSERT INTO user_skills (user_id, skill_id, years_experience, experience_level)
                            VALUES (%s, %s, %s, %s)
                        """
                        cursor.execute(skill_query, (user_id, skill_id, years, exp_level))

                conn.commit()
                cursor.close()
                conn.close()

                return jsonify({
                    'success': True, 
                    'message': 'Resume parsed, preprocessed, and mapping complete',
                    'total_experience': total_experience,
                    'experience_blocks': experience_blocks, 
                    'skill_experience': skill_experience,
                    'categorized_skills': categorized_skills,
                    'professional_summary': prof_summary,
                    'text_length': len(structured_text),
                    'preview': structured_text[:200] + '...' if len(structured_text) > 200 else structured_text
                }), 200
            else:
                return jsonify({'success': False, 'message': 'Could not extract text from PDF'}), 500
                
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error processing PDF: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'Invalid file type. Only PDF is supported for now.'}), 400
@resume_api.route('/user-skills/<int:user_id>', methods=['GET'])
def get_user_skills(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
            SELECT s.skill_name, us.experience_level, us.years_experience
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.id
            WHERE us.user_id = %s
        """
        cursor.execute(query, (user_id,))
        skills = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'skills': skills
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
