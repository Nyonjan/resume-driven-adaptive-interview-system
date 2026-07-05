document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('id');

    const loader = document.getElementById("resultsLoading");
    const content = document.getElementById("resultsContent");

    if (!sessionId) {
        window.location.href = "dashboard.html";
        return;
    }

    // Populate Sidebar
    const userFullName = localStorage.getItem("userFullName");
    if (document.getElementById("userName")) document.getElementById("userName").textContent = userFullName;

    // Fetch and render the overall summary and skill summary
    Promise.all([
        fetch(`http://127.0.0.1:5000/api/interview/results/${sessionId}`).then(res => res.json()),
        fetch(`http://127.0.0.1:5000/api/interview/results/${sessionId}/skills`).then(res => res.json()),
        fetch(`http://127.0.0.1:5000/api/interview/results/${sessionId}/difficulty`).then(res => res.json())
    ])
    .then(([overallData, skillData, difficultyData]) => {
        if (overallData.success && overallData.data) {
            renderOverallSummary(overallData.data);
            
            if (skillData.success && skillData.data) {
                renderSkillSummary(skillData.data);
            } else {
                console.warn("Skill summary data missing or error: ", skillData.message);
                document.getElementById("skillCards").innerHTML = "<p>No skill data available.</p>";
            }

            if (difficultyData.success && difficultyData.data) {
                renderDifficultySummary(difficultyData.data);
            } else {
                console.warn("Difficulty summary data missing or error: ", difficultyData.message);
                if(document.getElementById("difficultyCards")) {
                    document.getElementById("difficultyCards").innerHTML = "<p>No difficulty data available.</p>";
                }
            }

            loader.classList.add("hidden");
            content.classList.remove("hidden");
        } else {
            alert("Error loading results: " + (overallData.message || "Unknown error"));
        }
    })
    .catch(err => {
        console.error(err);
        alert("Failed to load interview results.");
    });

    function renderOverallSummary(summaryData) {
        document.getElementById("valTotal").textContent = summaryData.total_attempted;
        document.getElementById("valCorrect").textContent = summaryData.correct;
        document.getElementById("valWrong").textContent = summaryData.wrong;
        document.getElementById("valAccuracy").textContent = summaryData.accuracy + "%";
        document.getElementById("valDuration").textContent = summaryData.duration;
        document.getElementById("valRating").textContent = summaryData.rating;

        // Draw Donut Chart
        const ctx = document.getElementById('overallChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Correct', 'Wrong'],
                datasets: [{
                    data: [summaryData.correct, summaryData.wrong],
                    backgroundColor: ['#10b981', '#ef4444'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { family: "'Inter', sans-serif" }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                let label = context.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed !== null) {
                                    label += context.parsed + ' answers';
                                }
                                return label;
                            }
                        }
                    }
                }
            }
        });
    }

    function renderSkillSummary(skillsData) {
        const container = document.getElementById("skillCards");
        container.innerHTML = "";

        const labels = [];
        const accuracyData = [];
        const backgroundColors = [];

        skillsData.forEach(skill => {
            labels.push(skill.skill_name);
            accuracyData.push(skill.accuracy);

            let badgeClass = '';
            let barColor = '';
            
            if (skill.status === "Strong") {
                badgeClass = "badge-strong";
                barColor = "rgba(16, 185, 129, 0.8)"; // green
            } else if (skill.status === "Moderate") {
                badgeClass = "badge-moderate";
                barColor = "rgba(245, 158, 11, 0.8)"; // yellow
            } else {
                badgeClass = "badge-weak";
                barColor = "rgba(239, 68, 68, 0.8)"; // red
            }
            backgroundColors.push(barColor);

            const card = document.createElement("div");
            card.className = "skill-card";
            card.innerHTML = `
                <div class="skill-info">
                    <span class="skill-card-name">${skill.skill_name}</span>
                    <span class="skill-stats">
                        Attempted: <strong>${skill.total_attempted}</strong> | 
                        Correct: <strong class="text-success">${skill.correct}</strong> |
                        Accuracy: <strong>${skill.accuracy}%</strong>
                    </span>
                </div>
                <div class="skill-badge ${badgeClass}">${skill.status}</div>
            `;
            container.appendChild(card);
        });

        // Draw Bar Chart
        const ctx = document.getElementById('skillChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Accuracy (%)',
                    data: accuracyData,
                    backgroundColor: backgroundColors,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Accuracy %'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y + '% Accuracy';
                            }
                        }
                    }
                }
            }
        });
    }

    function renderDifficultySummary(diffData) {
        if (!diffData || !diffData.difficulties) return;

        const container = document.getElementById("difficultyCards");
        if (!container) return;
        container.innerHTML = "";

        const labels = [];
        const accuracyData = [];
        const backgroundColors = [];

        // Colors for easy, medium, hard
        const colorMap = {
            'easy': 'rgba(59, 130, 246, 0.8)', // blue
            'medium': 'rgba(139, 92, 246, 0.8)', // purple
            'hard': 'rgba(236, 72, 153, 0.8)' // pink
        };

        diffData.difficulties.forEach(diff => {
            labels.push(diff.difficulty);
            accuracyData.push(diff.accuracy);

            const colorKey = diff.difficulty.toLowerCase();
            backgroundColors.push(colorMap[colorKey] || 'rgba(156, 163, 175, 0.8)');

            const card = document.createElement("div");
            card.className = "difficulty-card";
            card.innerHTML = `
                <div class="difficulty-info">
                    <span class="difficulty-card-name">${diff.difficulty}</span>
                    <span class="difficulty-stats">
                        Attempted: <strong>${diff.total_attempted}</strong> | 
                        Correct: <strong class="text-success">${diff.correct}</strong> |
                        Accuracy: <strong>${diff.accuracy}%</strong>
                    </span>
                </div>
            `;
            container.appendChild(card);
        });

        // Add Insights
        const insightsContainer = document.getElementById("difficultyInsights");
        if (insightsContainer && diffData.insights) {
            insightsContainer.innerHTML = "";
            diffData.insights.forEach(insight => {
                const item = document.createElement("div");
                item.className = "insight-item";
                item.innerHTML = `<i class="fas fa-lightbulb" style="color: var(--primary-color); margin-right: 8px;"></i> ${insight}`;
                insightsContainer.appendChild(item);
            });
        }

        // Draw Chart
        const ctxElem = document.getElementById('difficultyChart');
        if (!ctxElem) return;
        const ctx = ctxElem.getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Accuracy (%)',
                    data: accuracyData,
                    backgroundColor: backgroundColors,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Accuracy %'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y + '% Accuracy';
                            }
                        }
                    }
                }
            }
        });
    }
});
