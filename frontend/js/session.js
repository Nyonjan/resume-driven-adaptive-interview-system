document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('id');

    if (!sessionId) {
        alert("Invalid Session. Redirecting to dashboard...");
        window.location.href = "dashboard.html";
        return;
    }

    const questionCard = document.getElementById("questionCard");
    const skillNameElem = document.getElementById("skillName");
    const expLevelElem = document.getElementById("expLevelBadge");
    const questionTextElem = document.getElementById("questionText");
    const optionsGrid = document.getElementById("optionsGrid");
    const nextBtn = document.getElementById("nextBtn");
    const currentIdxElem = document.getElementById("currentIdx");
    const totalQsElem = document.getElementById("totalQs");
    const progressBar = document.getElementById("progressBar");
    const sessionLoader = document.getElementById("sessionLoader");

    const confidenceSlider = document.getElementById("confidenceSlider");
    const confidenceValue = document.getElementById("confidenceValue");
    const confidenceEmoji = document.getElementById("confidenceEmoji");
    const confidenceMood = document.getElementById("confidenceMood");

    const moodMap = [
        { max: 0.1, emoji: "😰", mood: "Just Guessing",  color: "#ef4444" },
        { max: 0.2, emoji: "😬", mood: "Very Unsure",     color: "#f97316" },
        { max: 0.3, emoji: "🤔", mood: "Somewhat Unsure", color: "#eab308" },
        { max: 0.5, emoji: "😐", mood: "Neutral",         color: "#94a3b8" },
        { max: 0.6, emoji: "🙂", mood: "Pretty Good",     color: "#22d3ee" },
        { max: 0.7, emoji: "😊", mood: "Fairly Sure",     color: "#3b82f6" },
        { max: 0.9, emoji: "😎", mood: "Very Confident",  color: "#22c55e" },
        { max: 1.0, emoji: "🔥", mood: "Absolutely Sure!", color: "#16a34a" },
    ];

    function updateConfidenceUI(val) {
        const num = parseFloat(val);
        confidenceValue.textContent = num.toFixed(1);
        const match = moodMap.find(m => num <= m.max) || moodMap[moodMap.length - 1];
        confidenceEmoji.textContent = match.emoji;
        confidenceEmoji.style.transform = "scale(1.3)";
        setTimeout(() => confidenceEmoji.style.transform = "scale(1)", 150);
        confidenceMood.textContent = match.mood;
        confidenceMood.style.color = match.color;
        confidenceValue.style.background = match.color;
    }

    // Update confidence display
    confidenceSlider.oninput = () => {
        updateConfidenceUI(confidenceSlider.value);
    };
    updateConfidenceUI(confidenceSlider.value); // set initial state

    let currentQuestion = null;
    let selectedOption = null;
    let questionStartTime = null;
    let isAnswerSubmitted = false;

    // Load initial question
    loadNextQuestion();

    function loadNextQuestion() {
        showLoader(true);
        fetch(`http://127.0.0.1:5000/api/interview/next-question/${sessionId}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    renderQuestion(data.question);
                    updateProgress(data.question.current_question_index || 0, data.question.total_questions || 0);
                } else {
                    if (data.message.toLowerCase().includes("all planned") || 
                        data.message.toLowerCase().includes("completed") ||
                        data.message.toLowerCase().includes("no more unique")) {
                        // Finalize session on backend
                        finalizeSession(true);
                    } else {
                        alert("Error: " + data.message);
                    }
                }
                showLoader(false);
            })
            .catch(err => {
                console.error(err);
                alert("Failed to load question.");
                showLoader(false);
            });
    }

    function finalizeSession(autoRedirect = false) {
        fetch('http://127.0.0.1:5000/api/interview/end', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        })
            .then(res => res.json())
            .then(data => {
                if (autoRedirect) {
                    alert("🎉 Interview Completed! Redirecting to results...");
                    window.location.href = `results.html?id=${sessionId}`;
                }
            })
            .catch(err => console.error("Finalize error:", err));
    }

    function renderQuestion(q) {
        currentQuestion = q;
        selectedOption = null;
        isAnswerSubmitted = false;
        optionsGrid.classList.remove("submitted"); // Re-enable clicks
        
        // Reset Button to Submit
        nextBtn.innerHTML = 'Submit Answer <i class="fas fa-check"></i>';
        nextBtn.classList.add("disabled");
        nextBtn.disabled = true;

        // Reset confidence
        confidenceSlider.value = 0.5;
        updateConfidenceUI(0.5);

        skillNameElem.textContent = q.skill_name;
        


        const diffBadge = document.getElementById("difficultyBadge");
        diffBadge.textContent = q.difficulty.toUpperCase();
        diffBadge.className = `diff-badge ${q.difficulty.toLowerCase()}`;

        expLevelElem.textContent = q.experience_level.toUpperCase();
        expLevelElem.className = `exp-badge ${q.experience_level.toLowerCase()}`;
        questionTextElem.textContent = q.question;

        optionsGrid.innerHTML = "";
        const options = [q.option1, q.option2, q.option3, q.option4];

        options.forEach((opt, index) => {
            if (!opt) return;
            const button = document.createElement("div");
            button.className = "option-item";
            button.innerHTML = `
                <div class="option-prefix">${String.fromCharCode(65 + index)}</div>
                <div class="option-text">${opt}</div>
            `;
            button.onclick = () => selectOption(index + 1, button);
            optionsGrid.appendChild(button);
        });

        // Track start time
        questionStartTime = Date.now();
    }

    function selectOption(index, element) {
        if (isAnswerSubmitted) return; // Prevent selection change after submission
        selectedOption = index;
        document.querySelectorAll(".option-item").forEach(el => el.classList.remove("selected"));
        element.classList.add("selected");
        nextBtn.classList.remove("disabled");
        nextBtn.disabled = false;
    }

    function updateProgress(current, total) {
        // These might need to be fetched from session directly if not in question object
        // For now, let's assume we have them or use placeholders
        if (total > 0) {
            currentIdxElem.textContent = current;
            totalQsElem.textContent = total;
            const percentage = (current / total) * 100;
            progressBar.style.width = `${percentage}%`;
        }
    }

    nextBtn.onclick = () => {
        if (isAnswerSubmitted) {
            // Stage 2: Load next question
            loadNextQuestion();
            return;
        }

        // Stage 1: Submit Answer
        if (!selectedOption || !currentQuestion || nextBtn.disabled) return;

        nextBtn.classList.add("disabled");
        nextBtn.disabled = true;

        const responseTime = (Date.now() - questionStartTime) / 1000;
        const confidence = parseFloat(confidenceSlider.value);

        showLoader(true);
        fetch('http://127.0.0.1:5000/api/interview/submit-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                question_id: currentQuestion.id,
                selected_option: selectedOption,
                response_time: responseTime,
                confidence: confidence
            })
        })
            .then(res => res.json())
            .then(data => {
                showLoader(false); // Hide loader to show feedback
                if (data.success) {
                    isAnswerSubmitted = true;
                    optionsGrid.classList.add("submitted"); // Disable further option clicks
                    
                    // Show visual feedback
                    const options = document.querySelectorAll(".option-item");
                    options.forEach((opt, idx) => {
                        if (idx + 1 == data.correct_option) opt.classList.add("correct-feedback");
                        if (idx + 1 == selectedOption && !data.is_correct) opt.classList.add("incorrect-feedback");
                    });

                    // Update button for next stage
                    nextBtn.innerHTML = 'Next Question <i class="fas fa-arrow-right"></i>';
                    nextBtn.classList.remove("disabled");
                    nextBtn.disabled = false;
                } else {
                    alert("Submission error: " + data.message);
                    nextBtn.classList.remove("disabled");
                    nextBtn.disabled = false;
                }
            })
            .catch(err => {
                console.error(err);
                alert("Failed to submit answer.");
                showLoader(false);
                nextBtn.classList.remove("disabled");
                nextBtn.disabled = false;
            });
    };

    function showLoader(show) {
        if (show) sessionLoader.classList.remove("hidden");
        else sessionLoader.classList.add("hidden");
    }

    document.getElementById("exitBtn").onclick = () => {
        if (confirm("Are you sure you want to exit? Your progress will be saved.")) {
            window.location.href = "interview.html";
        }
    };
});
