document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const yearSelect = document.getElementById('year-select');
    const quizContainer = document.getElementById('quiz-container');
    const completionScreen = document.getElementById('completion-screen');
    
    const questionCountEl = document.getElementById('question-count');
    const progressFill = document.getElementById('progress-fill');
    const questionText = document.getElementById('question-text');
    const optionsContainer = document.getElementById('options-container');
    
    const feedbackBox = document.getElementById('feedback-box');
    const feedbackTitle = document.getElementById('feedback-title');
    const correctAnswerText = document.getElementById('correct-answer-text');
    
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const restartBtn = document.getElementById('restart-btn');

    // State
    let currentSession = null;
    let questions = [];
    let currentIndex = 0;
    // Stores the user's selected answer for a question to maintain state when navigating back and forth
    let userAnswers = {}; 

    // Initialization
    function init() {
        if (typeof quizData === 'undefined' || Object.keys(quizData).length === 0) {
            questionText.textContent = "Error: Quiz data not loaded.";
            return;
        }

        // Populate dropdown
        const sessions = Object.keys(quizData).sort((a, b) => {
            // Sort by year, then month roughly
            return a.localeCompare(b);
        });

        sessions.forEach(session => {
            const option = document.createElement('option');
            option.value = session;
            option.textContent = session;
            yearSelect.appendChild(option);
        });

        // Event Listeners
        yearSelect.addEventListener('change', (e) => loadSession(e.target.value));
        prevBtn.addEventListener('click', goPrev);
        nextBtn.addEventListener('click', goNext);
        restartBtn.addEventListener('click', () => loadSession(currentSession));

        // Load first session by default
        loadSession(sessions[0]);
    }

    function loadSession(sessionName) {
        currentSession = sessionName;
        questions = quizData[sessionName] || [];
        currentIndex = 0;
        userAnswers = {};
        
        quizContainer.classList.remove('hidden');
        completionScreen.classList.add('hidden');
        
        if (questions.length === 0) {
            questionText.textContent = "No questions found for this paper.";
            optionsContainer.innerHTML = '';
            return;
        }
        
        renderQuestion();
    }

    function renderQuestion() {
        if (currentIndex < 0 || currentIndex >= questions.length) return;

        const q = questions[currentIndex];
        
        // Update progress
        questionCountEl.textContent = `Question ${currentIndex + 1} of ${questions.length}`;
        const progressPercent = ((currentIndex + 1) / questions.length) * 100;
        progressFill.style.width = `${progressPercent}%`;

        // Update Question text
        questionText.innerHTML = `<strong>${q.id}.</strong> ${escapeHTML(q.text)}`;
        
        // Clear previous options
        optionsContainer.innerHTML = '';
        feedbackBox.className = 'feedback-box hidden';

        // Render options
        const optionsList = ['A', 'B', 'C', 'D'];
        optionsList.forEach(opt => {
            if (q.options[opt]) {
                const btn = document.createElement('button');
                btn.className = 'option-btn';
                btn.innerHTML = `<span class="opt-letter">${opt})</span> <span class="opt-text">${escapeHTML(q.options[opt])}</span>`;
                
                // If user already answered this question
                if (userAnswers[q.id]) {
                    btn.disabled = true;
                    if (opt === q.correct_answer) {
                        btn.classList.add('correct');
                    } else if (opt === userAnswers[q.id] && userAnswers[q.id] !== q.correct_answer) {
                        btn.classList.add('wrong');
                    }
                } else {
                    btn.addEventListener('click', () => handleOptionSelect(opt, q));
                }

                optionsContainer.appendChild(btn);
            }
        });

        // Show feedback if already answered
        if (userAnswers[q.id]) {
            showFeedback(userAnswers[q.id], q.correct_answer);
        }

        // Navigation state
        prevBtn.disabled = currentIndex === 0;
        
        if (currentIndex === questions.length - 1) {
            nextBtn.textContent = "Finish";
        } else {
            nextBtn.textContent = "Next";
        }
    }

    function handleOptionSelect(selectedOpt, question) {
        userAnswers[question.id] = selectedOpt;
        
        // Disable all buttons and highlight
        const buttons = optionsContainer.querySelectorAll('.option-btn');
        buttons.forEach(btn => {
            btn.disabled = true;
            const letter = btn.querySelector('.opt-letter').textContent.charAt(0);
            if (letter === question.correct_answer) {
                btn.classList.add('correct');
            } else if (letter === selectedOpt && selectedOpt !== question.correct_answer) {
                btn.classList.add('wrong');
            }
        });

        showFeedback(selectedOpt, question.correct_answer);
    }

    function showFeedback(selectedOpt, correctOpt) {
        feedbackBox.classList.remove('hidden', 'correct-fb', 'wrong-fb');
        
        if (selectedOpt === correctOpt) {
            feedbackBox.classList.add('correct-fb');
            feedbackTitle.textContent = "Correct!";
            correctAnswerText.textContent = "Great job.";
        } else {
            feedbackBox.classList.add('wrong-fb');
            feedbackTitle.textContent = "Incorrect";
            correctAnswerText.textContent = `The correct answer is ${correctOpt}.`;
        }
    }

    function goNext() {
        if (currentIndex < questions.length - 1) {
            currentIndex++;
            renderQuestion();
        } else {
            // Finish
            quizContainer.classList.add('hidden');
            completionScreen.classList.remove('hidden');
        }
    }

    function goPrev() {
        if (currentIndex > 0) {
            currentIndex--;
            renderQuestion();
        }
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }

    init();
});
