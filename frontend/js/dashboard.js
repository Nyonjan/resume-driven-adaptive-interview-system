document.addEventListener("DOMContentLoaded", function () {
    // Get user data from localStorage
    const userFullName = localStorage.getItem("userFullName");
    const userEmail = localStorage.getItem("userEmail");
    const userId = localStorage.getItem("userId");
    let currentRecommendedJobs = []; // Store jobs globally for modal selection

    if (!userFullName || !userEmail) {
        window.location.href = "index.html";
        return;
    }

    if (document.getElementById("userName")) document.getElementById("userName").textContent = userFullName;
    if (document.getElementById("userEmail")) document.getElementById("userEmail").textContent = userEmail;

    // Handle URL parameters for section switching
    const urlParams = new URLSearchParams(window.location.search);
    const sectionParam = urlParams.get('section');


    // Check for existing analysis data on load
    const savedAnalysis = localStorage.getItem("lastAnalysisResults");
    if (savedAnalysis) {
        try {
            const analysisData = JSON.parse(savedAnalysis);
            populateResults(analysisData, analysisData.fileName || "Stored Resume");
        } catch (e) {
            console.error("Error loading saved analysis:", e);
            localStorage.removeItem("lastAnalysisResults");
        }
    }

    // Section Switching Logic
    const sidebarLinks = document.querySelectorAll(".sidebar-nav a[data-section]");
    const contentViews = document.querySelectorAll(".content-view");

    sidebarLinks.forEach(link => {
        link.addEventListener("click", function (e) {
            const sectionId = this.getAttribute("data-section");
            if (!sectionId) return;

            e.preventDefault();

            // Update active state in sidebar
            sidebarLinks.forEach(l => l.parentElement.classList.remove("active"));
            this.parentElement.classList.add("active");

            // Show corresponding view
            contentViews.forEach(view => {
                if (view.id === `${sectionId}-view`) {
                    view.classList.remove("hidden");
                    // Trigger section-specific loading
                    if (sectionId === "dashboard") {
                        loadOverviewData(userId);
                    } else if (sectionId === "my-interviews") {
                        loadInterviewHistory(userId);
                    } else if (sectionId === "skill-analytics") {
                        loadSkillAnalytics(userId);
                    }
                } else {
                    view.classList.add("hidden");
                }
            });
        });
    });

    // Initial load - If no section param, load dashboard
    if (!sectionParam) {
        loadOverviewData(userId);
    }

    // Auto-switch to section if provided in URL
    if (sectionParam) {
        const targetLink = Array.from(sidebarLinks).find(link => link.getAttribute('data-section') === sectionParam);
        if (targetLink) {
            targetLink.click();
        }
    }

    // Dashboard Overview Functions
    async function loadOverviewData(uid) {
        const welcomeGreeting = document.getElementById("welcomeGreeting");
        if (!welcomeGreeting) return;

        try {
            const firstName = (userFullName || "User").split(" ")[0];
            welcomeGreeting.innerText = `Welcome back, ${firstName}!`;

            const response = await fetch(`http://127.0.0.1:5000/api/interview/overview/${uid}`);
            const result = await response.json();

            if (result.success) {
                const stats = result.data;
                document.getElementById("overviewTotalInterviews").innerText = stats.total_interviews;
                document.getElementById("overviewAvgAccuracy").innerText = `${stats.avg_accuracy}%`;
                document.getElementById("overviewReadinessScore").innerText = `${stats.readiness_score}%`;

                updateSuggestedStep(stats);
            }
        } catch (error) {
            console.error("Error loading overview stats:", error);
        }
    }

    function updateSuggestedStep(stats) {
        const title = document.getElementById("stepTitle");
        const desc = document.getElementById("stepDescription");
        const btn = document.querySelector("#suggestedStepContainer button");

        if (stats.total_interviews === 0) {
            title.innerText = "Complete your first interview";
            desc.innerText = "Practice with a job matched interview to see how you perform against real-world requirements.";
            btn.innerText = "Start Now";
            btn.onclick = () => document.querySelector('[data-section="my-interviews"]').click();
        } else if (stats.readiness_score < 60) {
            title.innerText = "Review your weak spots";
            desc.innerText = `Your readiness score is ${stats.readiness_score}%. Review your Skill Analytics to identify and practice your weakest areas.`;
            btn.innerText = "Check Analytics";
            btn.onclick = () => document.querySelector('[data-section="skill-analytics"]').click();
        } else if (stats.avg_accuracy >= 80) {
            title.innerText = "Challenge yourself";
            desc.innerText = "You're performing exceptionally well! Try a session with 'Hard' difficulty to further sharpen your skills.";
            btn.innerText = "Practice Hard Mode";
            btn.onclick = () => document.querySelector('[data-section="my-interviews"]').click();
        } else {
            title.innerText = "Keep the momentum going";
            desc.innerText = "Consistency is key to mastering interviews. Schedule a quick 10-minute practice session now.";
            btn.innerText = "Quick Practice";
            btn.onclick = () => document.querySelector('[data-section="my-interviews"]').click();
        }
    }


    async function loadInterviewHistory(userId) {
        const tableBody = document.getElementById("historyTableBody");
        if (!tableBody) return;

        try {
            const response = await fetch(`http://127.0.0.1:5000/api/interview/history/${userId}`);
            const result = await response.json();

            if (result.success && result.data.length > 0) {
                tableBody.innerHTML = result.data.map(session => `
                    <tr>
                        <td class="date-cell">${session.date}</td>
                        <td class="type-cell">${session.interview_type || 'General Skills'}</td>
                        <td>${session.total_questions}</td>
                        <td>${session.correct}</td>
                        <td class="accuracy-cell">${session.accuracy}%</td>
                        <td>
                            <span class="rating-badge rating-${session.rating.toLowerCase().replace(' ', '-')}">
                                ${session.rating}
                            </span>
                        </td>
                        <td class="action-cell">
                            <div class="action-buttons">
                                <a href="results.html?id=${session.session_id}" class="view-btn" title="View Feedback">
                                    <i class="fas fa-eye"></i>
                                </a>
                                <button class="retry-btn" onclick="retryInterview('${session.skills}', '${session.interview_type}')" title="Practice Again">
                                    <i class="fas fa-redo"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `).join('');
            }
            else if (result.success && result.data.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="6" class="no-history-cell">No interviews found. Complete your first interview to see feedback here!</td></tr>`;
            } else {
                tableBody.innerHTML = `<tr><td colspan="6" class="error-cell">Error: ${result.message}</td></tr>`;
            }
        } catch (error) {
            console.error("Error fetching history:", error);
            tableBody.innerHTML = `<tr><td colspan="6" class="error-cell">Failed to load history. Please check your connection.</td></tr>`;
        }
    }

    // Define retry function globally
    window.retryInterview = function (skillsString, type) {
        if (!skillsString || skillsString === 'null') {
            alert("⚠️ No skills recorded for this interview session.");
            return;
        }

        const skills = skillsString.split(', ');
        localStorage.setItem("targetInterviewSkills", JSON.stringify(skills));

        if (type && type !== 'General Skills' && type !== 'null') {
            localStorage.setItem("targetJobTitle", type);
        } else {
            localStorage.removeItem("targetJobTitle");
        }

        // Redirect to interview page
        window.location.href = "interview.html";
    };



    // Profile Form Logic
    const profileForm = document.getElementById("profileForm");
    const editProfileBtn = document.getElementById("editProfileBtn");
    const cancelEditBtn = document.getElementById("cancelEditBtn");
    const formActions = document.getElementById("formActions");
    const avatarActions = document.querySelector(".avatar-actions");
    const settingsInputs = document.querySelectorAll("#profileForm input:not([type='file'])");

    if (editProfileBtn) {
        editProfileBtn.addEventListener("click", function () {
            // Enable editing
            settingsInputs.forEach(input => {
                input.removeAttribute("readonly");
                input.style.paddingLeft = "12px"; // Restore padding
            });
            editProfileBtn.classList.add("hidden");
            formActions.classList.remove("hidden");
            if (avatarActions) avatarActions.classList.remove("hidden");
            settingsInputs[0].focus();
        });
    }

    if (cancelEditBtn) {
        cancelEditBtn.addEventListener("click", function () {
            // Revert changes
            document.getElementById("fullName").value = localStorage.getItem("userFullName") || "Jon Kon";
            document.getElementById("email").value = localStorage.getItem("userEmail") || "jon@gmail.com";

            // Disable editing
            disableEditing();
        });
    }

    function disableEditing() {
        settingsInputs.forEach(input => {
            input.setAttribute("readonly", true);
            input.style.paddingLeft = "0"; // Remove padding for cleaner readonly look
        });
        editProfileBtn.classList.remove("hidden");
        formActions.classList.add("hidden");
        if (avatarActions) avatarActions.classList.add("hidden");
    }

    if (profileForm) {
        profileForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const newName = document.getElementById("fullName").value;
            const newEmail = document.getElementById("email").value;

            localStorage.setItem("userFullName", newName);
            localStorage.setItem("userEmail", newEmail);

            // Update UI
            if (document.getElementById("userName")) document.getElementById("userName").textContent = newName;
            const emailSpan = document.querySelector(".user-profile .user-email");
            if (emailSpan) emailSpan.textContent = newEmail;

            // Disable editing after save
            disableEditing();
            showStatusMessage("Your profile has been updated!", "success");
        });
    }

    function showStatusMessage(text, type) {
        const msgEl = document.getElementById("settingsMessage");
        if (!msgEl) return;

        msgEl.textContent = text;
        msgEl.className = `settings-message ${type}`;
        msgEl.classList.remove("hidden");

        // Hide after 4 seconds
        setTimeout(() => {
            msgEl.classList.add("hidden");
        }, 4000);
    }

    // Avatar Logic
    const openAvatarModalBtn = document.getElementById("openAvatarModalBtn");
    const avatarModal = document.getElementById("avatarModal");
    const closeAvatarModal = document.getElementById("closeAvatarModal");
    const avatarGrid = document.getElementById("avatarGrid");
    const saveAvatarBtn = document.getElementById("saveAvatarBtn");
    const profilePreview = document.getElementById("profilePreview");
    const sidebarAvatar = document.getElementById("userAvatar");

    const availableAvatars = ["avatar1.png", "avatar2.png", "avatar3.png"];
    let currentAvatar = localStorage.getItem("userAvatar") || "avatar1.png";

    // Initial Load
    updateAvatarUI(currentAvatar);

    if (openAvatarModalBtn) {
        openAvatarModalBtn.addEventListener("click", () => {
            renderAvatarGrid();
            avatarModal.classList.remove("hidden");
        });
    }

    if (closeAvatarModal) {
        closeAvatarModal.addEventListener("click", () => {
            avatarModal.classList.add("hidden");
        });
    }

    // Close modal when clicking outside
    window.addEventListener("click", (event) => {
        if (event.target == avatarModal) {
            avatarModal.classList.add("hidden");
        }
    });

    function renderAvatarGrid() {
        if (!avatarGrid) return;
        avatarGrid.innerHTML = "";
        availableAvatars.forEach(avatar => {
            const div = document.createElement("div");
            div.className = `avatar-item ${avatar === currentAvatar ? 'selected' : ''}`;
            div.innerHTML = `<img src="../images/avatar/${avatar}" alt="${avatar}">`;
            div.onclick = () => {
                document.querySelectorAll(".avatar-item").forEach(el => el.classList.remove("selected"));
                div.classList.add("selected");
                currentAvatar = avatar;
            };
            avatarGrid.appendChild(div);
        });
    }

    if (saveAvatarBtn) {
        saveAvatarBtn.addEventListener("click", () => {
            fetch("http://127.0.0.1:5000/api/user/update-avatar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: userId, avatar: currentAvatar })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        localStorage.setItem("userAvatar", currentAvatar);
                        updateAvatarUI(currentAvatar);
                        avatarModal.classList.add("hidden");
                        showStatusMessage("Your avatar has been updated.", "success");
                    } else {
                        showStatusMessage("Oops! " + data.message, "error");
                    }
                })
                .catch(err => {
                    console.error("Error saving avatar:", err);
                    showStatusMessage("Something went wrong. Please check your connection.", "error");
                });
        });
    }

    function updateAvatarUI(avatarName) {
        const path = `../images/avatar/${avatarName}`;
        if (profilePreview) profilePreview.src = path;
        if (sidebarAvatar) sidebarAvatar.src = path;
    }

    // Change Password Logic
    const openPasswordModalBtn = document.getElementById("openChangePasswordModalBtn");
    const passwordModal = document.getElementById("passwordModal");
    const closePasswordModal = document.getElementById("closePasswordModal");
    const changePasswordForm = document.getElementById("changePasswordForm");

    if (openPasswordModalBtn) {
        openPasswordModalBtn.addEventListener("click", () => {
            if (passwordModal) passwordModal.classList.remove("hidden");
        });
    }

    if (closePasswordModal) {
        closePasswordModal.addEventListener("click", () => {
            if (passwordModal) passwordModal.classList.add("hidden");
        });
    }

    window.addEventListener("click", (event) => {
        if (event.target == passwordModal) {
            passwordModal.classList.add("hidden");
        }
    });

    if (changePasswordForm) {
        changePasswordForm.addEventListener("submit", function (e) {
            e.preventDefault();

            const currentPassword = document.getElementById("currentPassword").value;
            const newPassword = document.getElementById("newPassword").value;
            const confirmNewPassword = document.getElementById("confirmNewPassword").value;

            if (newPassword.length < 8) {
                showStatusMessage("New password must be at least 8 characters.", "error");
                return;
            }

            if (newPassword !== confirmNewPassword) {
                showStatusMessage("New passwords do not match.", "error");
                return;
            }

            fetch("http://127.0.0.1:5000/api/user/change-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: userId,
                    current_password: currentPassword,
                    new_password: newPassword
                })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showStatusMessage("Password updated successfully!", "success");
                        passwordModal.classList.add("hidden");
                        changePasswordForm.reset();
                    } else {
                        showStatusMessage("Error: " + data.message, "error");
                    }
                })
                .catch(err => {
                    console.error("Error changing password:", err);
                    showStatusMessage("Something went wrong. Please check your connection.", "error");
                });
        });
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

    // Re-upload Button
    const reUploadBtn = document.getElementById("reUploadBtn");
    if (reUploadBtn) {
        reUploadBtn.addEventListener("click", () => {
            localStorage.removeItem("lastAnalysisResults");
            document.getElementById("resultsView").style.display = "none";
            document.getElementById("uploadSection").style.display = "block";
            location.reload(); // Refresh to clear state
        });
    }

    // Drag and Drop Logic
    const uploadZone = document.getElementById("uploadZone");
    const fileInput = document.getElementById("fileInput");

    if (uploadZone && fileInput) {
        uploadZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            uploadZone.parentElement.classList.add("dragover");
        });

        uploadZone.addEventListener("dragleave", () => {
            uploadZone.parentElement.classList.remove("dragover");
        });

        uploadZone.addEventListener("drop", (e) => {
            e.preventDefault();
            uploadZone.parentElement.classList.remove("dragover");
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0]);
            }
        });

        fileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
            }
        });
    }

    function handleFileUpload(file) {
        if (!file) return;

        // Show loading state
        const uploadZone = document.getElementById("uploadZone");
        const originalContent = uploadZone.innerHTML;
        uploadZone.innerHTML = `
            <div class="upload-icon">
                <i class="fas fa-spinner fa-spin"></i>
            </div>
            <h3>Analyzing Your Resume...</h3>
            <p>Using AI to identify your skills and experience.</p>
        `;

        const formData = new FormData();
        formData.append("file", file);
        formData.append("user_id", userId);

        fetch("http://127.0.0.1:5000/api/resume/upload", {
            method: "POST",
            body: formData
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Store results for persistence
                    result.fileName = file.name;
                    localStorage.setItem("lastAnalysisResults", JSON.stringify(result));
                    populateResults(result, file.name);
                } else {
                    alert("Error: " + result.message);
                    uploadZone.innerHTML = originalContent;
                }
            })
            .catch(error => {
                console.error("Error:", error);
                alert("Error during file upload: " + error.message);
                uploadZone.innerHTML = originalContent;
            });
    }

    function populateResults(data, fileName) {
        // Switch Views
        document.getElementById("uploadSection").style.display = "none";
        document.getElementById("resultsView").style.display = "block";
        document.getElementById("reUploadBtn").style.display = "block";

        // Update Header/Status
        const fileStatus = document.querySelector(".file-name-status");
        if (fileStatus) fileStatus.textContent = `"${fileName}" successfully parsed using Neural Engine v4.2`;

        // Update Technical Proficiency (with bars)
        const techList = document.getElementById("techSkillsList");
        techList.innerHTML = "";
        const techSkills = data.categorized_skills.technical_proficiency || [];

        techSkills.forEach((skill, index) => {
            const level = classifyExp(skill.years);
            const percentage = Math.min(100, (skill.years / 5) * 100);

            const skillDiv = document.createElement("div");
            skillDiv.className = "skill-item";
            if (index >= 4) {
                skillDiv.style.display = "none";
                skillDiv.classList.add("extra-skill");
            }
            skillDiv.innerHTML = `
                <div class="skill-info">
                    <span class="skill-name">${skill.name}</span>
                    <span class="skill-lvl">${level}</span>
                </div>
                <div class="skill-bar">
                    <div class="skill-bar-fill" style="width: ${percentage}%"></div>
                </div>
            `;
            techList.appendChild(skillDiv);
        });

        // Handle Toggle Button
        const toggleContainer = document.getElementById("techSkillsToggleContainer");
        const toggleBtn = document.getElementById("techSkillsToggleBtn");

        if (techSkills.length > 4) {
            toggleContainer.style.display = "block";
            toggleBtn.onclick = function () {
                const extras = document.querySelectorAll(".extra-skill");
                const isHidden = extras[0].style.display === "none";

                extras.forEach(el => el.style.display = isHidden ? "block" : "none");
                this.innerHTML = isHidden ?
                    `See Less <i class="fas fa-chevron-up"></i>` :
                    `See More <i class="fas fa-chevron-down"></i>`;
            };
        } else {
            toggleContainer.style.display = "none";
        }

        // Update Frameworks & Tools (Tags)
        const frameworksList = document.getElementById("frameworksList");
        frameworksList.innerHTML = "";
        const frameworks = data.categorized_skills.frameworks_tools || [];
        frameworks.forEach(skill => {
            const span = document.createElement("span");
            span.className = "skill-tag";
            span.textContent = skill.name;
            frameworksList.appendChild(span);
        });

        // Update Soft Skills (Tags)
        const softSkillsList = document.getElementById("softSkillsList");
        softSkillsList.innerHTML = "";
        const softSkills = data.categorized_skills.soft_skills || [];
        softSkills.forEach(skill => {
            const span = document.createElement("span");
            span.className = "skill-tag soft";
            span.textContent = skill.name;
            softSkillsList.appendChild(span);
        });

        // Update Experience
        document.getElementById("totalExpValue").textContent = data.total_experience;
        const timeline = document.getElementById("expTimeline");
        timeline.innerHTML = "";

        const blocks = data.experience_blocks || [];
        blocks.forEach(block => {
            const li = document.createElement("li");
            // Basic extraction of title/company from block_text if possible, or just use years
            const yearsText = `${block.start_year} - ${block.end_year === new Date().getFullYear() ? 'Present' : block.end_year}`;
            li.innerHTML = `<b>${yearsText}</b>: Detected experience (${block.duration} years)`;
            timeline.appendChild(li);
        });

        // Automatically load job recommendations
        loadJobRecommendations(userId);
    }

    function loadJobRecommendations(uid) {
        const section = document.getElementById("jobRecommendationsSection");
        const tableBody = document.getElementById("jobsTableBody");

        if (!section || !tableBody) return;

        section.style.display = "block";
        tableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 40px;"><i class="fas fa-spinner fa-spin"></i> Analyzing job matches...</td></tr>`;

        fetch(`http://127.0.0.1:5000/api/job/recommend?user_id=${uid}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let jobs = data.recommended_jobs;
                    // Sort by match percentage descending
                    jobs.sort((a, b) => b.skill_match_percent - a.skill_match_percent);

                    currentRecommendedJobs = jobs; // Cache for modal
                    if (jobs.length === 0) {
                        tableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 40px;">No matching jobs found for your experience level yet.</td></tr>`;
                    } else {
                        tableBody.innerHTML = "";
                        jobs.forEach(job => {
                            const matchPercent = job.skill_match_percent;
                            const row = document.createElement("tr");

                            row.innerHTML = `
                                <td class="job-title-cell">${job.job_title}</td>
                                <td class="match-pct-cell">${matchPercent}%</td>
                                <td>
                                    <div class="skills-cell">
                                        ${job.matched_skills.map(s => `<span class="mini-tag match">${s}</span>`).join('')}
                                    </div>
                                </td>
                                <td>
                                    <div class="skills-cell">
                                        ${job.missing_skills.map(s => `<span class="mini-tag missing">${s}</span>`).join('')}
                                    </div>
                                </td>
                            `;
                            tableBody.appendChild(row);
                        });
                    }
                } else {
                    tableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: red; padding: 20px;">Error: ${data.message}</td></tr>`;
                }
            })
            .catch(error => {
                console.error("Error fetching jobs:", error);
                tableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: red; padding: 20px;">Could not fetch recommendations.</td></tr>`;
            });
    }

    // Global chart instances
    let radarChart = null;
    let difficultyChart = null;
    let trendChart = null;

    async function loadSkillAnalytics(uid) {
        const filter = document.getElementById("analyticsFilter")?.value || 'overall';
        const grid = document.querySelector(".analytics-dashboard-grid");

        try {
            const response = await fetch(`http://127.0.0.1:5000/api/interview/analytics/${uid}?filter=${filter}`);
            const result = await response.json();

            if (result.success) {
                updateAnalyticsUI(result.data);
            } else {
                console.error("Failed to load analytics:", result.message);
            }
        } catch (error) {
            console.error("Error loading analytics:", error);
        }
    }

    function updateAnalyticsUI(data) {
        const { skills, difficulty, trend } = data;

        // 1. Update Stat Cards
        if (skills && skills.length > 0) {
            const sorted = [...skills].sort((a, b) => b.accuracy - a.accuracy);
            document.getElementById("strongestSkill").innerText = sorted[0].skill_name;
            document.getElementById("weakestSkill").innerText = sorted[sorted.length - 1].skill_name;

            const lowPerf = skills.filter(s => s.accuracy < 60);
            document.getElementById("focusArea").innerText = lowPerf.length > 0 ? lowPerf[0].skill_name : "General Practice";
        } else {
            document.getElementById("strongestSkill").innerText = "--";
            document.getElementById("weakestSkill").innerText = "--";
            document.getElementById("focusArea").innerText = "--";
        }

        // 2. Render Skills List
        const listContainer = document.getElementById("analyticsSkillsList");
        if (skills && skills.length > 0) {
            listContainer.innerHTML = skills.slice(0, 6).map(s => `
                <div class="skill-item" style="margin-bottom: 5px;">
                    <div class="skill-info" style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-weight: 600; font-size: 0.9rem; color: var(--text-dark);">${s.skill_name}</span>
                        <span style="font-weight: 700; font-size: 0.9rem; color: var(--primary-green);">${s.accuracy}%</span>
                    </div>
                    <div class="skill-bar" style="height: 6px; background: #f1f5f9; border-radius: 4px;">
                        <div class="skill-bar-fill" style="height: 100%; width: ${s.accuracy}%; background: var(--primary-green); border-radius: 4px; transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);"></div>
                    </div>
                </div>
            `).join('');
        } else {
            listContainer.innerHTML = `<p style="text-align: center; padding: 40px; color: var(--text-gray);">No data available for this period.</p>`;
        }

        // 3. Render Charts
        renderRadarChart(skills || []);
        renderDifficultyChart(difficulty || { easy: 0, medium: 0, hard: 0 });
        renderTrendChart(trend || []);
    }

    function renderRadarChart(skills) {
        const canvas = document.getElementById('radarChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (radarChart) radarChart.destroy();

        const displaySkills = skills.length > 0 ? skills.slice(0, 5) : [{ skill_name: 'Python', accuracy: 0 }, { skill_name: 'SQL', accuracy: 0 }, { skill_name: 'Linux', accuracy: 0 }, { skill_name: 'APIs', accuracy: 0 }, { skill_name: 'Cloud', accuracy: 0 }];
        const labels = displaySkills.map(s => s.skill_name);
        const dataValues = displaySkills.map(s => s.accuracy);

        radarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Technical Profile',
                    data: dataValues,
                    backgroundColor: 'rgba(76, 175, 80, 0.15)',
                    borderColor: '#4CAF50',
                    borderWidth: 2,
                    pointBackgroundColor: '#4CAF50',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#4CAF50',
                    pointRadius: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    r: {
                        angleLines: { color: '#f1f5f9' },
                        grid: { color: '#f1f5f9' },
                        suggestedMin: 0,
                        suggestedMax: 100,
                        ticks: { display: false },
                        pointLabels: {
                            font: { size: 10, weight: '600' },
                            color: '#64748b'
                        }
                    }
                }
            }
        });
    }

    function renderDifficultyChart(diffData) {
        const canvas = document.getElementById('difficultyBarChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (difficultyChart) difficultyChart.destroy();

        difficultyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Easy', 'Medium', 'Hard'],
                datasets: [{
                    data: [diffData.easy, diffData.medium, diffData.hard],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                    borderRadius: 6,
                    barThickness: 35
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#f1f5f9', drawBorder: false },
                        ticks: { font: { size: 10 }, color: '#94a3b8', callback: v => v + '%' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11, weight: '600' }, color: '#64748b' }
                    }
                }
            }
        });
    }

    function renderTrendChart(trendData) {
        const canvas = document.getElementById('trendLineChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (trendChart) trendChart.destroy();

        const labels = trendData.length > 0 ? trendData.map(d => d.date) : ['01/01', '01/05', '01/10'];
        const values = trendData.length > 0 ? trendData.map(d => d.accuracy) : [0, 0, 0];

        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.05)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#4CAF50',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#f1f5f9', drawBorder: false },
                        ticks: { font: { size: 10 }, color: '#94a3b8', callback: v => v + '%' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 10 }, color: '#94a3b8' }
                    }
                }
            }
        });
    }

    // Add event listener for the filter
    document.addEventListener("change", function (e) {
        if (e.target && e.target.id === "analyticsFilter") {
            loadSkillAnalytics(localStorage.getItem("userId"));
        }
    });

    function classifyExp(years) {
        if (years < 1) return "Fresher";
        if (years < 3) return "Junior";
        if (years < 6) return "Mid";
        return "Senior";
    }

    // Practice Button Listeners
    const practiceMatchBtn = document.getElementById("practiceMatchBtn");
    const practiceOverallBtn = document.getElementById("practiceOverallBtn");
    const jobModal = document.getElementById("jobModal");
    const closeModal = document.getElementById("closeModal");
    const jobSelectionList = document.getElementById("jobSelectionList");

    if (practiceMatchBtn) {
        practiceMatchBtn.addEventListener("click", () => {
            if (currentRecommendedJobs.length === 0) {
                alert("⚠️ Please upload your resume first to see job recommendations.");
                return;
            }
            renderJobSelectionModal();
            jobModal.classList.remove("hidden");
        });
    }

    if (closeModal) {
        closeModal.onclick = () => jobModal.classList.add("hidden");
    }

    window.onclick = (event) => {
        if (event.target == jobModal) jobModal.classList.add("hidden");
    };

    function renderJobSelectionModal() {
        jobSelectionList.innerHTML = "";
        jobSelectionList.className = "job-selection-list";
        currentRecommendedJobs.sort((a, b) => b.skill_match_percent - a.skill_match_percent);
        currentRecommendedJobs.forEach((job, index) => {
            const item = document.createElement("div");
            item.className = "job-selection-item vertical";
            item.innerHTML = `
                <div class="job-card-icon">
                    <i class="fas fa-briefcase"></i>
                </div>
                <div class="job-info">
                    <h4>${job.job_title}</h4>
                    <div class="job-meta">
                        <span class="match-badge">${job.skill_match_percent}% Match</span>
                    </div>
                </div>
            `;
            item.onclick = () => selectJobForPractice(job);
            jobSelectionList.appendChild(item);
        });
    }

    function selectJobForPractice(job) {
        // Get the selected test scope
        const scopeSelector = document.querySelector('input[name="testScope"]:checked');
        const scope = scopeSelector ? scopeSelector.value : 'all';

        let targetSkills = [];
        if (scope === 'all') {
            targetSkills = [...new Set([...job.matched_skills, ...job.missing_skills])];
        } else {
            targetSkills = [...new Set(job.matched_skills)];
        }

        if (targetSkills.length === 0) {
            alert("⚠️ No matched skills available for this job. Please choose 'All Job Skills'.");
            return;
        }

        localStorage.setItem("targetInterviewSkills", JSON.stringify(targetSkills));
        localStorage.setItem("jobMatchedSkills", JSON.stringify(job.matched_skills));
        localStorage.setItem("jobMissingSkills", JSON.stringify(job.missing_skills));
        localStorage.setItem("jobScope", scope);
        const jobTitleDisplay = scope === 'matched' ? `${job.job_title} (Matched Skills Only)` : job.job_title;
        localStorage.setItem("targetJobTitle", jobTitleDisplay);
        window.location.href = "interview.html";
    }

    if (practiceOverallBtn) {
        practiceOverallBtn.addEventListener("click", () => {
            localStorage.removeItem("targetInterviewSkills");
            localStorage.removeItem("targetJobTitle");
            window.location.href = "interview.html";
        });
    }
});
