
document.addEventListener("DOMContentLoaded", function () {

  /* =========================
     Get Modal Elements
  ========================= */

  const signupModal = document.getElementById("signupModal");
  const signinModal = document.getElementById("signinModal");

  /* =========================
     Get Buttons
  ========================= */

  const gettingStartedBtn = document.getElementById("gettingStartedBtn");
  const closeSignupModal = document.getElementById("closeSignupModal");
  const closeSigninModal = document.getElementById("closeSigninModal");
  const goToSignin = document.getElementById("goToSignin");
  const goToSignup = document.getElementById("goToSignup");

  /* =========================
     Modal Open Logic
  ========================= */

  if (gettingStartedBtn && signupModal && signinModal) {
    gettingStartedBtn.addEventListener("click", function () {
      signupModal.style.display = "flex";
      signinModal.style.display = "none";
    });
  }

  /* =========================
     Close Modal Logic
  ========================= */

  if (closeSignupModal && signupModal) {
    closeSignupModal.addEventListener("click", function () {
      signupModal.style.display = "none";
    });
  }

  if (closeSigninModal && signinModal) {
    closeSigninModal.addEventListener("click", function () {
      signinModal.style.display = "none";
    });
  }

  /* =========================
     Close Modal When Clicking Outside
  ========================= */

  window.addEventListener("click", function (event) {
    if (signupModal && event.target === signupModal) {
      signupModal.style.display = "none";
    }

    if (signinModal && event.target === signinModal) {
      signinModal.style.display = "none";
    }
  });

  /* =========================
     Switch Between Modals
  ========================= */

  if (goToSignin && signupModal && signinModal) {
    goToSignin.addEventListener("click", function () {
      signupModal.style.display = "none";
      signinModal.style.display = "flex";
    });
  }

  if (goToSignup && signupModal && signinModal) {
    goToSignup.addEventListener("click", function () {
      signinModal.style.display = "none";
      signupModal.style.display = "flex";
    });
  }

  /* =========================
     Sign Up Form
  ========================= */

  const signupForm = document.getElementById("signupForm");

  if (signupForm) {
    signupForm.addEventListener("submit", function (event) {
      event.preventDefault();

      const fullName = document.getElementById("fullName")?.value.trim();
      const email = document.getElementById("signupEmail")?.value.trim();
      const password = document.getElementById("signupPassword")?.value;
      const confirmPassword = document.getElementById("confirmPassword")?.value;

      let errors = [];

      if (!fullName) {
        errors.push("Full Name is required.");
      }

      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

      if (!emailPattern.test(email)) {
        errors.push("Please enter a valid email address (e.g., name@example.com).");
      }

      if (!password || password.length < 8) {
        errors.push("Password must be at least 8 characters.");
      }

      if (password !== confirmPassword) {
        errors.push("Passwords do not match.");
      }

      if (errors.length > 0) {
        alert(errors.join("\n"));
        return;
      }

      const data = {
        fullName,
        email,
        password
      };

      fetch("http://127.0.0.1:5000/api/auth/signup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      })
        .then(response => response.json())
        .then(result => {
          if (result.success) {
            window.location.href = "index.html";
          } else {
            alert("Error: " + result.message);
          }
        })
        .catch(error => {
          alert("Error during signup: " + error.message);
        });
    });
  }

  /* =========================
     Sign In Form
  ========================= */

  const signinForm = document.getElementById("signinForm");

  if (signinForm) {
    signinForm.addEventListener("submit", function (event) {
      event.preventDefault();

      const email = document.getElementById("signinEmail")?.value.trim();
      const password = document.getElementById("signinPassword")?.value;

      const data = {
        email,
        password
      };

      fetch("http://127.0.0.1:5000/api/auth/signin", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      })
        .then(response => response.json())
        .then(result => {
          if (result.success) {
            localStorage.setItem("userId", result.user.id);
            localStorage.setItem("userFullName", result.user.fullName);
            localStorage.setItem("userEmail", result.user.email);
            localStorage.setItem("userAvatar", result.user.avatar || "avatar1.png");
            window.location.href = "dashboard.html";
          } else {
            alert("Error: " + result.message);
          }
        })
        .catch(error => {
          console.error("Error:", error);
          alert("Error during sign in: " + error.message);
        });
    });
  }

  /* =========================
     Load Site Config (Images, Branding)
  ========================= */
  fetch("http://127.0.0.1:5000/api/admin/settings/public", { cache: "no-store" })
    .then(res => res.json())
    .then(data => {
      if (data.success && data.settings) {
        const s = data.settings;

        // Branding
        if (s.site_name) {
          const logoEl = document.getElementById("siteLogoName");
          if (logoEl) logoEl.textContent = s.site_name;
          document.title = `${s.site_name} - Interview Practice Assistant`;
        }
        if (s.site_tagline) {
          const taglineEl = document.getElementById("heroTagline");
          if (taglineEl) taglineEl.textContent = s.site_tagline;
        }

        // Hero Image (background on .hero section)
        if (s.hero_image_url) {
          const heroSec = document.querySelector(".hero");
          if (heroSec) heroSec.style.backgroundImage = `linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('${s.hero_image_url}')`;
        }

        // Target Audience Images
        if (s.audience_1_image_url) {
          const img = document.getElementById("img-audience-1");
          if (img) img.src = s.audience_1_image_url;
        }
        if (s.audience_2_image_url) {
          const img = document.getElementById("img-audience-2");
          if (img) img.src = s.audience_2_image_url;
        }
        if (s.audience_3_image_url) {
          const img = document.getElementById("img-audience-3");
          if (img) img.src = s.audience_3_image_url;
        }

        // Advantage Images
        if (s.advantage_1_image_url) {
          const img = document.getElementById("img-advantage-1");
          if (img) img.src = s.advantage_1_image_url;
        }
        if (s.advantage_2_image_url) {
          const img = document.getElementById("img-advantage-2");
          if (img) img.src = s.advantage_2_image_url;
        }
        if (s.advantage_3_image_url) {
          const img = document.getElementById("img-advantage-3");
          if (img) img.src = s.advantage_3_image_url;
        }
      }
    })
    .catch(err => console.error("Error loading site config:", err));

});