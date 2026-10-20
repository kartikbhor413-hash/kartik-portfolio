/**
 * ==============================================================================
 * KARTIK BHOR PORTFOLIO - CLIENT-SIDE SCRIPT
 * Full Stack Developer & AI Engineer
 * ==============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // State Management
  const state = {
    sessionToken: null,
    targetEmail: '',
    expiresInSeconds: 300,
    resendCooldown: 45,
    timerInterval: null,
    cooldownInterval: null,
    isSubmitting: false
  };

  // ----------------------------------------------------------------------------
  // 1. MOBILE NAVIGATION TOGGLE
  // ----------------------------------------------------------------------------
  const hamburgerBtn = document.getElementById('hamburgerBtn');
  const navMenu = document.getElementById('navMenu');
  const navLinks = document.querySelectorAll('.nav-link');

  if (hamburgerBtn && navMenu) {
    hamburgerBtn.addEventListener('click', () => {
      const isOpen = navMenu.classList.toggle('open');
      hamburgerBtn.classList.toggle('open', isOpen);
      hamburgerBtn.setAttribute('aria-expanded', String(isOpen));
    });

    // Close menu when a link is clicked
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        navMenu.classList.remove('open');
        hamburgerBtn.classList.remove('open');
        hamburgerBtn.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // ----------------------------------------------------------------------------
  // 2. ACTIVE NAVIGATION HIGHLIGHT ON SCROLL
  // ----------------------------------------------------------------------------
  const sections = document.querySelectorAll('section[id], header[id]');
  window.addEventListener('scroll', () => {
    const scrollY = window.pageYOffset;
    sections.forEach(current => {
      const sectionHeight = current.offsetHeight;
      const sectionTop = current.offsetTop - 120;
      const sectionId = current.getAttribute('id');
      const activeLink = document.querySelector(`.nav-link[href*="${sectionId}"]`);
      if (activeLink && scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
        navLinks.forEach(l => l.classList.remove('active'));
        activeLink.classList.add('active');
      }
    });
  }, { passive: true });

  // ----------------------------------------------------------------------------
  // 3. TYPING EFFECT FOR HERO ROLE
  // ----------------------------------------------------------------------------
  const typedRole = document.getElementById('typedRole');
  if (typedRole) {
    const roles = [
      'Full Stack Developer & AI Engineer',
      'Computer Vision & OCR Builder',
      'Python & Flask Architect',
      'Supabase & PostgreSQL Engineer',
      'Open-Source System Creator'
    ];
    let roleIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let typingSpeed = 90;

    function typeEffect() {
      const currentRole = roles[roleIndex];
      if (isDeleting) {
        typedRole.textContent = currentRole.substring(0, charIndex - 1);
        charIndex--;
        typingSpeed = 45;
      } else {
        typedRole.textContent = currentRole.substring(0, charIndex + 1);
        charIndex++;
        typingSpeed = 90;
      }

      if (!isDeleting && charIndex === currentRole.length) {
        typingSpeed = 2200; // Hold at full text
        isDeleting = true;
      } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        roleIndex = (roleIndex + 1) % roles.length;
        typingSpeed = 500; // Pause before typing next
      }

      setTimeout(typeEffect, typingSpeed);
    }

    // Start typing after initial entrance
    setTimeout(typeEffect, 1200);
  }

  // ----------------------------------------------------------------------------
  // 4. SCROLL REVEAL ANIMATIONS (IntersectionObserver)
  // ----------------------------------------------------------------------------
  const revealElements = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('active');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.12,
      rootMargin: '0px 0px -40px 0px'
    });

    revealElements.forEach(el => revealObserver.observe(el));
  } else {
    revealElements.forEach(el => el.classList.add('active'));
  }

  // ----------------------------------------------------------------------------
  // 5. RESUME PREVIEW MODAL
  // ----------------------------------------------------------------------------
  const resumeModal = document.getElementById('resumeModal');
  const resumeModalBtn = document.getElementById('resumeModalBtn');
  const resumeModalClose = document.getElementById('resumeModalClose');

  if (resumeModal && resumeModalBtn) {
    resumeModalBtn.addEventListener('click', () => {
      resumeModal.classList.add('active');
      resumeModal.setAttribute('aria-hidden', 'false');
    });

    const closeModal = () => {
      resumeModal.classList.remove('active');
      resumeModal.setAttribute('aria-hidden', 'true');
    };

    if (resumeModalClose) resumeModalClose.addEventListener('click', closeModal);
    resumeModal.addEventListener('click', (e) => {
      if (e.target === resumeModal) closeModal();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && resumeModal.classList.contains('active')) {
        closeModal();
      }
    });
  }

  // ----------------------------------------------------------------------------
  // 6. CONTACT FORM & TWO-STEP OTP VERIFICATION
  // ----------------------------------------------------------------------------
  const contactForm = document.getElementById('contactForm');
  const otpForm = document.getElementById('otpForm');
  const step1Container = document.getElementById('step1Container');
  const step2Container = document.getElementById('step2Container');
  const stepSuccessContainer = document.getElementById('stepSuccessContainer');

  const nameInput = document.getElementById('nameInput');
  const emailInput = document.getElementById('emailInput');
  const subjectInput = document.getElementById('subjectInput');
  const messageInput = document.getElementById('messageInput');
  const charCount = document.getElementById('charCount');

  const sendOtpBtn = document.getElementById('sendOtpBtn');
  const verifyOtpBtn = document.getElementById('verifyOtpBtn');
  const resendOtpBtn = document.getElementById('resendOtpBtn');
  const backToStep1Btn = document.getElementById('backToStep1Btn');
  const sendAnotherBtn = document.getElementById('sendAnotherBtn');

  const step1Status = document.getElementById('step1Status');
  const step2Status = document.getElementById('step2Status');
  const targetEmailDisplay = document.getElementById('targetEmailDisplay');
  const timerDisplay = document.getElementById('timerDisplay');
  const resendCountdown = document.getElementById('resendCountdown');
  const otpBoxes = document.querySelectorAll('.otp-box');

  // Live message character count
  if (messageInput && charCount) {
    messageInput.addEventListener('input', () => {
      charCount.textContent = messageInput.value.length;
    });
  }

  // Helper: Clear field errors
  function clearErrors() {
    document.querySelectorAll('.field-error').forEach(el => el.textContent = '');
    if (step1Status) {
      step1Status.textContent = '';
      step1Status.className = 'form-status';
    }
    if (step2Status) {
      step2Status.textContent = '';
      step2Status.className = 'form-status';
    }
  }

  // Helper: Validation
  function validateStep1() {
    clearErrors();
    let isValid = true;

    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const subject = subjectInput.value.trim();
    const message = messageInput.value.trim();

    if (!name || name.length < 2) {
      document.getElementById('nameError').textContent = 'Please enter your name (min. 2 characters).';
      isValid = false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !emailRegex.test(email)) {
      document.getElementById('emailError').textContent = 'Please enter a valid email address.';
      isValid = false;
    }

    if (!subject || subject.length < 2) {
      document.getElementById('subjectError').textContent = 'Please enter a subject.';
      isValid = false;
    }

    if (!message || message.length < 10) {
      document.getElementById('messageError').textContent = 'Message should be at least 10 characters long.';
      isValid = false;
    }

    return isValid;
  }

  // Timer: 5-minute expiry countdown
  function startExpiryTimer(seconds = 300) {
    clearInterval(state.timerInterval);
    state.expiresInSeconds = seconds;

    const updateDisplay = () => {
      const mins = Math.floor(state.expiresInSeconds / 60);
      const secs = state.expiresInSeconds % 60;
      if (timerDisplay) {
        timerDisplay.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
      }

      if (state.expiresInSeconds <= 0) {
        clearInterval(state.timerInterval);
        if (timerDisplay) timerDisplay.textContent = 'Expired';
        if (step2Status) {
          step2Status.textContent = 'Verification code has expired. Please click Resend Code.';
          step2Status.className = 'form-status error';
        }
      }
      state.expiresInSeconds--;
    };

    updateDisplay();
    state.timerInterval = setInterval(updateDisplay, 1000);
  }

  // Timer: 45-second resend cooldown
  function startResendCooldown(seconds = 45) {
    clearInterval(state.cooldownInterval);
    state.resendCooldown = seconds;
    if (resendOtpBtn) resendOtpBtn.disabled = true;

    const updateDisplay = () => {
      if (resendCountdown) resendCountdown.textContent = state.resendCooldown;

      if (state.resendCooldown <= 0) {
        clearInterval(state.cooldownInterval);
        if (resendOtpBtn) {
          resendOtpBtn.disabled = false;
          resendOtpBtn.textContent = 'Resend Code';
        }
      } else {
        if (resendOtpBtn) {
          resendOtpBtn.textContent = `Resend Code (${state.resendCooldown}s)`;
        }
      }
      state.resendCooldown--;
    };

    updateDisplay();
    state.cooldownInterval = setInterval(updateDisplay, 1000);
  }

  // STEP 1 SUBMIT: Send OTP
  if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (state.isSubmitting) return;

      if (!validateStep1()) return;

      state.isSubmitting = true;
      sendOtpBtn.classList.add('loading');
      sendOtpBtn.disabled = true;
      step1Status.textContent = 'Validating and generating verification code...';
      step1Status.className = 'form-status';

      const payload = {
        name: nameInput.value.trim(),
        email: emailInput.value.trim(),
        subject: subjectInput.value.trim(),
        message: messageInput.value.trim()
      };

      try {
        const response = await fetch('/api/send-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.success) {
          state.sessionToken = data.session_token;
          state.targetEmail = payload.email;

          if (targetEmailDisplay) {
            targetEmailDisplay.textContent = payload.email;
          }

          // Transition to Step 2
          step1Container.style.display = 'none';
          step2Container.style.display = 'block';

          // Reset OTP boxes to empty
          otpBoxes.forEach(box => {
            box.value = '';
            box.classList.remove('filled');
          });
          if (otpBoxes[0]) otpBoxes[0].focus();

          // Start timers
          startExpiryTimer(data.expires_in || 300);
          startResendCooldown(45);

          step2Status.textContent = data.message || 'Verification code sent to your email!';
          step2Status.className = 'form-status success';
        } else {
          step1Status.textContent = data.error || 'Failed to send verification code. Please try again.';
          step1Status.className = 'form-status error';
        }
      } catch (err) {
        console.error('Send OTP Error:', err);
        step1Status.textContent = 'Network or server error. Please check your connection and try again.';
        step1Status.className = 'form-status error';
      } finally {
        state.isSubmitting = false;
        sendOtpBtn.classList.remove('loading');
        sendOtpBtn.disabled = false;
      }
    });
  }

  // OTP BOXES INTERACTION (Auto advance, backspace, paste)
  otpBoxes.forEach((box, idx) => {
    box.addEventListener('input', (e) => {
      const val = e.target.value.replace(/[^0-9]/g, '');
      box.value = val ? val[val.length - 1] : '';

      if (box.value) {
        box.classList.add('filled');
        if (idx < otpBoxes.length - 1) {
          otpBoxes[idx + 1].focus();
        }
      } else {
        box.classList.remove('filled');
      }
    });

    box.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace' && !box.value && idx > 0) {
        otpBoxes[idx - 1].focus();
      } else if (e.key === 'ArrowLeft' && idx > 0) {
        otpBoxes[idx - 1].focus();
      } else if (e.key === 'ArrowRight' && idx < otpBoxes.length - 1) {
        otpBoxes[idx + 1].focus();
      }
    });

    box.addEventListener('paste', (e) => {
      e.preventDefault();
      const pasted = (e.clipboardData || window.clipboardData).getData('text');
      const digits = pasted.replace(/[^0-9]/g, '').slice(0, otpBoxes.length);

      if (digits.length > 0) {
        digits.split('').forEach((digit, i) => {
          if (otpBoxes[i]) {
            otpBoxes[i].value = digit;
            otpBoxes[i].classList.add('filled');
          }
        });
        const nextIndex = Math.min(digits.length, otpBoxes.length - 1);
        otpBoxes[nextIndex].focus();
      }
    });
  });

  // RESEND OTP ACTION
  if (resendOtpBtn) {
    resendOtpBtn.addEventListener('click', async () => {
      if (resendOtpBtn.disabled || !state.sessionToken) return;

      resendOtpBtn.disabled = true;
      step2Status.textContent = 'Sending a new verification code...';
      step2Status.className = 'form-status';

      try {
        const response = await fetch('/api/resend-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_token: state.sessionToken })
        });

        const data = await response.json();

        if (response.ok && data.success) {
          startExpiryTimer(data.expires_in || 300);
          startResendCooldown(45);
          step2Status.textContent = data.message || 'New code sent successfully!';
          step2Status.className = 'form-status success';
          otpBoxes.forEach(b => {
            b.value = '';
            b.classList.remove('filled');
          });
          if (otpBoxes[0]) otpBoxes[0].focus();
        } else {
          step2Status.textContent = data.error || 'Failed to resend code.';
          step2Status.className = 'form-status error';
          resendOtpBtn.disabled = false;
        }
      } catch (err) {
        console.error('Resend OTP Error:', err);
        step2Status.textContent = 'Failed to resend verification code. Please try again.';
        step2Status.className = 'form-status error';
        resendOtpBtn.disabled = false;
      }
    });
  }

  // BACK TO STEP 1 BUTTON
  if (backToStep1Btn) {
    backToStep1Btn.addEventListener('click', () => {
      clearInterval(state.timerInterval);
      clearInterval(state.cooldownInterval);
      step2Container.style.display = 'none';
      step1Container.style.display = 'block';
      clearErrors();
    });
  }

  // STEP 2 SUBMIT: Verify OTP
  if (otpForm) {
    otpForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (state.isSubmitting) return;

      clearErrors();

      // Gather OTP
      let enteredOtp = '';
      otpBoxes.forEach(box => enteredOtp += box.value.trim());

      const otpError = document.getElementById('otpError');
      if (enteredOtp.length !== 6) {
        if (otpError) otpError.textContent = 'Please enter all 6 digits of the verification code.';
        return;
      }

      state.isSubmitting = true;
      verifyOtpBtn.classList.add('loading');
      verifyOtpBtn.disabled = true;
      step2Status.textContent = 'Verifying security code...';
      step2Status.className = 'form-status';

      try {
        const response = await fetch('/api/verify-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_token: state.sessionToken,
            otp: enteredOtp
          })
        });

        const data = await response.json();

        if (response.ok && data.success) {
          clearInterval(state.timerInterval);
          clearInterval(state.cooldownInterval);

          step2Container.style.display = 'none';
          stepSuccessContainer.style.display = 'block';

          const successText = document.getElementById('successMessageText');
          if (successText && data.message) {
            successText.textContent = data.message;
          }

          // Reset form inputs
          contactForm.reset();
          if (charCount) charCount.textContent = '0';
        } else {
          step2Status.textContent = data.error || 'Invalid code. Please try again.';
          step2Status.className = 'form-status error';
          if (otpError) otpError.textContent = data.error || 'Verification failed.';
          
          // Focus first empty or all
          otpBoxes.forEach(b => b.classList.add('error'));
          setTimeout(() => otpBoxes.forEach(b => b.classList.remove('error')), 1500);
        }
      } catch (err) {
        console.error('Verify OTP Error:', err);
        step2Status.textContent = 'Network error while verifying. Please try again.';
        step2Status.className = 'form-status error';
      } finally {
        state.isSubmitting = false;
        verifyOtpBtn.classList.remove('loading');
        verifyOtpBtn.disabled = false;
      }
    });
  }

  // STEP 3: Send Another Message
  if (sendAnotherBtn) {
    sendAnotherBtn.addEventListener('click', () => {
      stepSuccessContainer.style.display = 'none';
      step1Container.style.display = 'block';
      clearErrors();
      state.sessionToken = null;
    });
  }

});
