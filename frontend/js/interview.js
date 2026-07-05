document.addEventListener("DOMContentLoaded", function () {
    const userFullName = localStorage.getItem("userFullName");
    const userEmail = localStorage.getItem("userEmail");
    const userId = localStorage.getItem("userId");

    if (!userFullName || !userId) {
        window.location.href = "index.html";
        return;
    }

    // Populate Sidebar
    if (document.getElementById("userName")) document.getElementById("userName").textContent = userFullName;
    if (document.getElementById("welcomeName")) document.getElementById("welcomeName").textContent = userFullName.split(' ')[0];
    if (document.getElementById("userEmail")) document.getElementById("userEmail").textContent = userEmail;

    // Avatar Logic
    const userAvatar = localStorage.getItem("userAvatar");
    if (userAvatar && document.getElementById("userAvatar")) {
        document.getElementById("userAvatar").src = `../images/avatar/${userAvatar}`;
    }

    // Logout Functionality
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", function () {
            localStorage.removeItem("userId");
            localStorage.removeItem("userFullName");
            localStorage.removeItem("userEmail");
            localStorage.removeItem("userAvatar");
            localStorage.removeItem("lastAnalysisResults");
            window.location.href = "index.html";
        });
    }

    // Check for Job Practice Context
    const targetSkills = JSON.parse(localStorage.getItem("targetInterviewSkills") || "[]");
    const targetJobTitle = localStorage.getItem("targetJobTitle");
    const jobMatchedSkills = JSON.parse(localStorage.getItem("jobMatchedSkills") || "[]");
    const jobMissingSkills = JSON.parse(localStorage.getItem("jobMissingSkills") || "[]");
    const jobScope = localStorage.getItem("jobScope");

    const interviewHero = document.querySelector(".interview-hero");
    if (targetJobTitle) {
        const jobContextCard = document.getElementById("jobContextCard");
        const displayJobTitle = document.getElementById("displayJobTitle");
        const matchedContainer = document.getElementById("matchedSkillsPills");
        const missingHeroContainer = document.getElementById("missingSkillsPillsHero");

        const missingSection = document.getElementById("missingSkillsSection");
        const missingContainer = document.getElementById("missingSkillsPills");

        const heroSubtitle = document.getElementById("heroSubtitle");
        const skillsSummaryCard = document.querySelector(".skills-summary-card");
        const toggleAllBtn = document.getElementById("toggleAllMissing");

        if (jobContextCard) {
            jobContextCard.classList.remove("hidden");
            displayJobTitle.textContent = targetJobTitle.replace(' (Matched Skills Only)', '');
            heroSubtitle.textContent = "Your interview has been tailored for this specific job opportunity.";

            // Render Matched Skills (Fixed in Hero)
            matchedContainer.innerHTML = jobMatchedSkills.map(skill => `<span class="skill-pill match">${skill}</span>`).join('');

            // Handle Missing Skills
            if (jobMissingSkills.length > 0) {
                // 1. Show static badges in Hero
                missingHeroContainer.innerHTML = jobMissingSkills.map(skill => `<span class="skill-pill missing-static">${skill}</span>`).join('');

                // 2. Show interactive selection card below
                missingSection.classList.remove("hidden");
                const shouldSelectAll = jobScope === 'all';

                missingContainer.innerHTML = jobMissingSkills.map(skill => `
                    <div class="skill-pill selectable missing ${shouldSelectAll ? 'selected' : ''}" data-skill="${skill}">
                        <i class="fas ${shouldSelectAll ? 'fa-check-circle' : 'fa-circle'}"></i>
                        <span>${skill}</span>
                    </div>
                `).join('');

                // Add Click Listeners
                missingContainer.querySelectorAll(".skill-pill.selectable").forEach(pill => {
                    pill.addEventListener("click", () => {
                        pill.classList.toggle("selected");
                        const icon = pill.querySelector("i");
                        if (pill.classList.contains("selected")) {
                            icon.className = "fas fa-check-circle";
                        } else {
                            icon.className = "fas fa-circle";
                        }

                        const allSelected = Array.from(missingContainer.querySelectorAll(".skill-pill.selectable"))
                            .every(p => p.classList.contains("selected"));
                        if (toggleAllBtn) toggleAllBtn.textContent = allSelected ? "Remove All" : "Include All";
                    });
                });

                if (toggleAllBtn) {
                    toggleAllBtn.textContent = shouldSelectAll ? "Remove All" : "Include All";
                    toggleAllBtn.addEventListener("click", () => {
                        const allSelected = Array.from(missingContainer.querySelectorAll(".skill-pill.selectable"))
                            .every(p => p.classList.contains("selected"));

                        missingContainer.querySelectorAll(".skill-pill.selectable").forEach(pill => {
                            const icon = pill.querySelector("i");
                            if (allSelected) {
                                pill.classList.remove("selected");
                                icon.className = "fas fa-circle";
                            } else {
                                pill.classList.add("selected");
                                icon.className = "fas fa-check-circle";
                            }
                        });
                        toggleAllBtn.textContent = allSelected ? "Include All" : "Remove All";
                    });
                }
            } else {
                missingHeroContainer.parentElement.style.display = "none";
                missingSection.classList.add("hidden");
            }

            if (skillsSummaryCard) skillsSummaryCard.style.display = "none";
        }
    } else {
        if (interviewHero) interviewHero.classList.add("overall-mode");
    }

    // Mode Selection Logic
    const modeCards = document.querySelectorAll(".mode-card");
    let selectedMode = "standard";

    modeCards.forEach(card => {
        card.addEventListener("click", () => {
            modeCards.forEach(c => c.classList.remove("selected"));
            card.classList.add("selected");
            selectedMode = card.dataset.mode;
        });
    });

    const skillsListContainer = document.getElementById("skillsListContainer");

    const selectAllCheckbox = document.getElementById("selectAllCheckbox");

    // Fetch Skills from Backend
    fetch(`http://127.0.0.1:5000/api/resume/user-skills/${userId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderSkills(data.skills);
            } else {
                skillsListContainer.innerHTML = `<div class="error-msg">Error loading skills: ${data.message}</div>`;
            }
        })
        .catch(err => {
            console.error("Fetch Error:", err);
            skillsListContainer.innerHTML = `<div class="error-msg">Failed to connect to the server.</div>`;
        });

    function renderSkills(skills) {
        if (!skills || skills.length === 0) {
            skillsListContainer.innerHTML = '<div class="no-skills-msg">No skills found. Please upload your resume first.</div>';
            return;
        }

        skillsListContainer.innerHTML = ""; // Clear loader

        skills.forEach(skill => {
            const isTargeted = targetSkills.length === 0 || targetSkills.includes(skill.skill_name);
            const card = document.createElement("div");
            card.className = isTargeted ? "interview-skill-card selected" : "interview-skill-card";
            card.dataset.skillId = skill.skill_id || "";
            card.dataset.skillName = skill.skill_name;

            const levelClass = skill.experience_level.toLowerCase();

            card.innerHTML = `
                <input type="checkbox" class="skill-checkbox" ${isTargeted ? 'checked' : ''}>
                <div class="skill-content">
                    <div class="skill-info">
                        <span class="skill-name">${skill.skill_name}</span>
                        <span class="skill-exp">${skill.years_experience} Yrs</span>
                    </div>
                    <div class="skill-level-badge ${levelClass}">
                        ${skill.experience_level.toUpperCase()}
                    </div>
                </div>
            `;

            // Card Click Event (Toggle Selection)
            card.addEventListener("click", (e) => {
                if (e.target.tagName !== "INPUT") {
                    const checkbox = card.querySelector(".skill-checkbox");
                    checkbox.checked = !checkbox.checked;
                    toggleCardSelection(card, checkbox.checked);
                }
            });

            // Checkbox Click Event
            const checkbox = card.querySelector(".skill-checkbox");
            checkbox.addEventListener("change", () => {
                toggleCardSelection(card, checkbox.checked);
            });

            skillsListContainer.appendChild(card);
        });

        updateSelectAllState();
    }

    function toggleCardSelection(card, isSelected) {
        if (isSelected) {
            card.classList.add("selected");
        } else {
            card.classList.remove("selected");
        }
        updateSelectAllState();
    }

    function updateSelectAllState() {
        const total = document.querySelectorAll(".skill-checkbox").length;
        const checked = document.querySelectorAll(".skill-checkbox:checked").length;
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = total === checked && total > 0;
            selectAllCheckbox.indeterminate = checked > 0 && checked < total;
        }
    }

    // Select All Toggle
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener("change", () => {
            const isChecked = selectAllCheckbox.checked;
            document.querySelectorAll(".skill-checkbox").forEach(cb => {
                cb.checked = isChecked;
                const card = cb.closest(".interview-skill-card");
                if (isChecked) card.classList.add("selected");
                else card.classList.remove("selected");
            });
        });
    }

    const startBtn = document.getElementById("startInterviewBtn");
    if (startBtn) {
        startBtn.addEventListener("click", () => {
            let selectedSkills = [];
            if (targetJobTitle) {
                // Collect Matched Skills
                const matched = Array.from(document.querySelectorAll("#matchedSkillsPills .skill-pill"))
                    .map(p => p.textContent.trim());

                // Collect Selected Missing Skills
                const selectedMissing = Array.from(document.querySelectorAll("#missingSkillsPills .skill-pill.selected"))
                    .map(p => p.dataset.skill);

                selectedSkills = [...matched, ...selectedMissing];
            } else {
                selectedSkills = Array.from(document.querySelectorAll(".skill-checkbox:checked"))
                    .map(cb => cb.closest(".interview-skill-card").dataset.skillName);
            }

            if (selectedSkills.length === 0) {
                alert("⚠️ Please select at least one skill to start the interview.");
                return;
            }

            // Start Interview API Call
            startBtn.disabled = true;
            startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Initializing...';

            fetch('http://127.0.0.1:5000/api/interview/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: userId,
                    selected_skills: selectedSkills,
                    mode: selectedMode
                })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Redirect to the actual interview session page
                        window.location.href = `session.html?id=${data.session_id}`;
                    } else {
                        alert(`❌ Failed to start session: ${data.message}`);
                        startBtn.disabled = false;
                        startBtn.innerHTML = '<i class="fas fa-play"></i> Start Interview';
                    }
                })
                .catch(err => {
                    console.error("Session Start Error:", err);
                    alert("❌ A server error occurred. Please try again.");
                    startBtn.disabled = false;
                    startBtn.innerHTML = '<i class="fas fa-play"></i> Start Interview';
                });
        });
    }
});
