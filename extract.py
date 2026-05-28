import re
import json

def extract_data(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    papers = {}
    current_session = None
    in_answer_key = False
    
    current_q_num = None
    current_q_text = ""
    current_options = {'A': '', 'B': '', 'C': '', 'D': ''}
    current_opt_letter = None

    ans_key_pattern = re.compile(r'ANSWER KEYS?', re.IGNORECASE)
    qn_pattern = re.compile(r'^(\d+)\.\s*(.*)')
    opt_pattern = re.compile(r'^([A-D])\)\s*(.*)')
    
    def save_current_q():
        nonlocal current_q_num, current_q_text, current_options, current_opt_letter
        if current_session and current_q_num and current_q_text.strip():
            if current_session not in papers:
                papers[current_session] = {'questions': {}, 'answers': {}}
            
            # Clean up text
            q_text = current_q_text.strip()
            opts = {k: v.strip() for k, v in current_options.items()}
            
            papers[current_session]['questions'][current_q_num] = {
                'text': q_text,
                'options': opts
            }
        current_q_num = None
        current_q_text = ""
        current_options = {'A': '', 'B': '', 'C': '', 'D': ''}
        current_opt_letter = None

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        if "STATE ELIGIBILITY TEST" in line_clean and re.search(r'20[1-2][0-9]', line_clean):
            save_current_q()
            # Extract Year and Month
            year_match = re.search(r'(20[1-2][0-9])', line_clean)
            month_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*', line_clean, re.IGNORECASE)
            
            if year_match:
                year = year_match.group(1)
                month = month_match.group(1).capitalize() if month_match else ''
                # Normalize months
                if month.startswith('Jan'): month = 'January'
                elif month.startswith('Feb'): month = 'February'
                elif month.startswith('Jun'): month = 'June'
                elif month.startswith('Jul'): month = 'July'
                elif month.startswith('Dec'): month = 'December'
                
                if int(year) >= 2015:
                    current_session = f"{year} {month}".strip()
                    in_answer_key = False
                    if current_session not in papers:
                        papers[current_session] = {'questions': {}, 'answers': {}}
            continue

        if ans_key_pattern.search(line_clean):
            save_current_q()
            in_answer_key = True
            continue
            
        if not current_session:
            continue
            
        if in_answer_key:
            tokens = line_clean.split()
            if 'ans_tokens' not in papers[current_session]:
                papers[current_session]['ans_tokens'] = []
            papers[current_session]['ans_tokens'].extend(tokens)
        else:
            # Question Parsing
            qn_match = qn_pattern.match(line_clean)
            if qn_match:
                q_num = qn_match.group(1)
                # Only accept if it's a new question and the number is greater than current (or current is None)
                if q_num not in papers[current_session]['questions'] and (not current_q_num or int(q_num) > int(current_q_num)):
                    save_current_q()
                    current_q_num = q_num
                    current_q_text = qn_match.group(2) + " "
                    continue
                else:
                    # Treat as part of current question/option
                    if current_opt_letter:
                        current_options[current_opt_letter] += line_clean + " "
                    else:
                        current_q_text += line_clean + " "
                    continue
                
            opt_match = opt_pattern.match(line_clean)
            if opt_match and current_q_num:
                current_opt_letter = opt_match.group(1)
                current_options[current_opt_letter] += opt_match.group(2) + " "
                continue
                
            # Continuation of text
            if current_q_num:
                if current_opt_letter:
                    inline_opts = list(re.finditer(r'\s+([A-D])\)(.*?)(?=\s+[A-D]\)|$)', line_clean))
                    if inline_opts:
                        for m in inline_opts:
                            let = m.group(1)
                            txt = m.group(2)
                            current_options[let] += txt + " "
                            current_opt_letter = let
                    else:
                        current_options[current_opt_letter] += line_clean + " "
                else:
                    inline_opts = list(re.finditer(r'\s+([A-D])\)(.*?)(?=\s+[A-D]\)|$)', line_clean))
                    if inline_opts:
                        first_opt_start = inline_opts[0].start()
                        if first_opt_start > 0:
                            current_q_text += line_clean[:first_opt_start] + " "
                        for m in inline_opts:
                            let = m.group(1)
                            txt = m.group(2)
                            current_options[let] += txt + " "
                            current_opt_letter = let
                    else:
                        current_q_text += line_clean + " "

    save_current_q()

    # Process answer tokens
    for session, data in papers.items():
        if 'ans_tokens' in data:
            tokens = data['ans_tokens']
            i = 0
            while i < len(tokens):
                t = tokens[i]
                if t.isdigit():
                    q_num = t
                    i += 1
                    while i < len(tokens) and not re.match(r'^[A-D]$|X|Cancelled|False|True', tokens[i], re.IGNORECASE):
                        if tokens[i].isdigit():
                            break
                        i += 1
                    if i < len(tokens) and not tokens[i].isdigit():
                        data['answers'][q_num] = tokens[i].upper()
                        i += 1
                else:
                    i += 1
            del data['ans_tokens']

    # Filter out empty or invalid sessions
    final_papers = {}
    for session, data in papers.items():
        print(f"Session {session}: Questions={len(data['questions'])}, Answers={len(data['answers'])}")
        if len(data["questions"]) > 10 and len(data["answers"]) > 10:
            valid_qs = {}
            for qn, qdata in data['questions'].items():
                if qn in data['answers']:
                    qdata['correct_answer'] = data['answers'][qn]
                    valid_qs[qn] = qdata
            
            q_list = []
            for qn in sorted(valid_qs.keys(), key=lambda x: int(x)):
                q_list.append({
                    'id': qn,
                    'text': valid_qs[qn]['text'].strip(),
                    'options': {k: v.strip() for k, v in valid_qs[qn]['options'].items()},
                    'correct_answer': valid_qs[qn]['correct_answer']
                })
            
            if q_list:
                final_papers[session] = q_list

    with open('data.js', 'w', encoding='utf-8') as f:
        f.write("const quizData = " + json.dumps(final_papers, indent=2) + ";")
    print(f"Extraction complete. Found {len(final_papers)} sessions.")
    for s, qs in final_papers.items():
        print(f" - {s}: {len(qs)} questions")

if __name__ == '__main__':
    extract_data('extracted_text.txt')
