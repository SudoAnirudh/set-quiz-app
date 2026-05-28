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
    
    ans_key_pattern = re.compile(r'ANSWER KEYS?', re.IGNORECASE)
    qn_pattern = re.compile(r'^(\d+)\.\s+(.*)')
    
    # Matches options anywhere in the line, provided they have spaces before them or are at the start
    opt_pattern = re.compile(r'(?:^|\s+)([A-D])\)\s*(.*?)(?=(?:\s+[A-D]\))|$)')

    def save_current_q():
        nonlocal current_q_num, current_q_text, current_options
        if current_session and current_q_num and current_q_text.strip():
            if current_session not in papers:
                papers[current_session] = {'questions': {}, 'answers': {}}
            
            q_text = current_q_text.strip()
            opts = {k: v.strip() for k, v in current_options.items()}
            
            papers[current_session]['questions'][current_q_num] = {
                'text': q_text,
                'options': opts
            }
        current_q_num = None
        current_q_text = ""
        current_options = {'A': '', 'B': '', 'C': '', 'D': ''}

    for line in lines:
        # Don't strip yet so we can check for indentation
        clean_line = line.strip()
        
        # Skip headers/footers
        if "t.me/joinchat" in clean_line or "SPS@MGU" in clean_line or "Compiled by" in clean_line or "120 MINUTES" in clean_line:
            continue
        if "STATE ELIGIBILITY TEST" in clean_line and "Syllabus" not in clean_line:
            pass # We will handle session detection
            
        if not clean_line:
            continue

        if "STATE ELIGIBILITY TEST" in clean_line and re.search(r'20[1-2][0-9]', clean_line):
            save_current_q()
            year_match = re.search(r'(20[1-2][0-9])', clean_line)
            month_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*', clean_line, re.IGNORECASE)
            
            if year_match:
                year = year_match.group(1)
                month = month_match.group(1).capitalize() if month_match else ''
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

        if ans_key_pattern.search(clean_line):
            save_current_q()
            in_answer_key = True
            continue
            
        if not current_session:
            continue
            
        if in_answer_key:
            tokens = clean_line.split()
            if 'ans_tokens' not in papers[current_session]:
                papers[current_session]['ans_tokens'] = []
            papers[current_session]['ans_tokens'].extend(tokens)
        else:
            # Check if this line starts a new question
            # Using strip() here since sometimes numbers might be indented slightly
            qn_match = qn_pattern.match(clean_line)
            if qn_match:
                q_num = qn_match.group(1)
                if q_num not in papers[current_session]['questions'] and (not current_q_num or int(q_num) > int(current_q_num)):
                    save_current_q()
                    current_q_num = q_num
                    
                    # The rest of the line might contain text and even options!
                    remainder = qn_match.group(2)
                    # Check if there are options on this same line
                    opts_on_line = list(opt_pattern.finditer(remainder))
                    if opts_on_line:
                        # Extract the question text before the first option
                        first_opt_start = opts_on_line[0].start()
                        current_q_text = remainder[:first_opt_start].strip() + " "
                        for m in opts_on_line:
                            current_options[m.group(1)] += m.group(2).strip() + " "
                    else:
                        current_q_text = remainder + " "
                    continue

            # If it's not a new question, it belongs to the current question or its options
            if current_q_num:
                # Find all options on this line
                # But wait, options are like `A) Option A       B) Option B`
                # So we can search the original unstripped line to see if there are gaps
                opts_on_line = list(opt_pattern.finditer(line))
                if opts_on_line:
                    # If there's text BEFORE the first option, it could be part of the question text
                    # but only if it's not mostly whitespace.
                    first_opt_start = opts_on_line[0].start()
                    before_text = line[:first_opt_start].strip()
                    
                    # But wait, what if the previous line had an option, and THIS line has text before the next option?
                    # Example:
                    # A) An option     B) Another option
                    #    that is long     that is also long
                    # pdftotext -layout puts "that is long" under A) and "that is also long" under B)
                    # This is tricky. So let's just use simple opt_pattern on the line.
                    # Actually, if there are NO options starting on this line, but there's text,
                    # we can look at its physical indentation!
                    pass

                # simpler approach: Just look for A), B), C), D) anywhere
                opts_on_line = list(opt_pattern.finditer(clean_line))
                if opts_on_line:
                    first_opt_start = opts_on_line[0].start()
                    before_text = clean_line[:first_opt_start].strip()
                    if before_text:
                        # Before text could belong to the previously active option OR the question
                        # If we haven't seen any options yet, it's question text.
                        # If we have, it's weird to have text before a new option on the same line,
                        # but we append it to the question just in case.
                        if not any(current_options.values()):
                            current_q_text += before_text + " "
                        
                    for m in opts_on_line:
                        current_options[m.group(1)] += m.group(2).strip() + " "
                else:
                    # No new options on this line.
                    # Does this line belong to an option or the question?
                    # If we haven't seen A) yet, it's question text.
                    if not current_options['A']:
                        current_q_text += clean_line + " "
                    else:
                        # It belongs to the most recently seen option? Or maybe it's just garbage.
                        # In pdftotext -layout, text for A is on the left, B is on the right.
                        # To perfectly parse layout is hard. We will just append to the question text 
                        # or all active options...
                        # Actually, a simple heuristic: if it's indented far right, it's B or D.
                        # For now, let's just append it to option A or C if it's on the left, etc.
                        # Actually, let's just look at the line and split by double spaces!
                        parts = re.split(r'\s{3,}', clean_line)
                        if len(parts) == 1:
                            if not current_options['C']:
                                current_options['A'] += " " + clean_line
                            else:
                                current_options['C'] += " " + clean_line
                        elif len(parts) >= 2:
                            if not current_options['C']:
                                current_options['A'] += " " + parts[0]
                                current_options['B'] += " " + parts[1]
                            else:
                                current_options['C'] += " " + parts[0]
                                current_options['D'] += " " + parts[1]

    save_current_q()

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

    final_papers = {}
    for session, data in papers.items():
        if len(data['questions']) > 10 and len(data['answers']) > 10:
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

if __name__ == '__main__':
    extract_data('extracted_text_layout.txt')
