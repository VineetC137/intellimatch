// Form validation and processing feedback
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const cvInput = document.getElementById('cv');
    const jobTitleSelect = document.getElementById('job_title');

    // Store event listeners for cleanup
    const formSubmitHandler = function(e) {
        if (!validateForm()) {
            e.preventDefault();
            return;
        }

        // Show processing state
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...';
        submitBtn.disabled = true;
        uploadForm.classList.add('processing');
    };

    if (uploadForm) {
        uploadForm.addEventListener('submit', formSubmitHandler);

    function validateForm() {
        let isValid = true;

        // Validate CV file
        if (cvInput) {
            const file = cvInput.files[0];
            if (!file) {
                showError(cvInput, 'Please select a CV file');
                isValid = false;
            } else if (!file.type.match('application/pdf')) {
                showError(cvInput, 'Only PDF files are allowed');
                isValid = false;
            } else if (file.size > 16 * 1024 * 1024) { // 16MB
                showError(cvInput, 'File size must be less than 16MB');
                isValid = false;
            } else {
                clearError(cvInput);
            }
        }

        // Validate job title selection
        if (jobTitleSelect) {
            if (!jobTitleSelect.value) {
                showError(jobTitleSelect, 'Please select a job title');
                isValid = false;
            } else {
                clearError(jobTitleSelect);
            }
        }

        return isValid;
    }

    function showError(element, message) {
        clearError(element);
        element.classList.add('is-invalid');
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        element.parentNode.appendChild(feedback);
    }

    function clearError(element) {
        element.classList.remove('is-invalid');
        const feedback = element.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }

    // Add input event listeners for real-time validation
    if (cvInput) {
        cvInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                if (!file.type.match('application/pdf')) {
                    showError(this, 'Only PDF files are allowed');
                } else if (file.size > 16 * 1024 * 1024) {
                    showError(this, 'File size must be less than 16MB');
                } else {
                    clearError(this);
                }
            }
        });
    }

    if (jobTitleSelect) {
        jobTitleSelect.addEventListener('change', function() {
            if (this.value) {
                clearError(this);
            }
        });
    }
    }
});