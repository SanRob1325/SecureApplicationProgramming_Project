// Main Javascript for application

document.addEventListener('DOMContentLoaded', function(){
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.map(function (tooltipTriggerEl){
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })

    // Password visibility toggle for generic password fields
    const passwordToggles = document.querySelectorAll('.password-toggle')

    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function(){
            const targetId = this.getAttribute('data-target')
            const passwordField = document.getElementById(targetId)
            const toggleIcon = this.querySelector('i')

            if(passwordField.type === 'password'){
                passwordField.type = 'text'
                toggleIcon.className = 'fa-eye-slash';
            } else{
                passwordField.type = 'password'
                toggleIcon.className ='fas fa-eye'
            }
        })
    })

    // Copy to clipboard for generic copy buttons
    const copyButtons = document.querySelectorAll('.copy-button')

    copyButtons.forEach(button => {
        button.addEventListener('click', function(){
            const targetId = this.getAttribute('data-target')
            const textField = document.getElementById(targetId)

            // Save the field type if its a password
            const isPassword = textField.type === 'password'

            // Make it visible if it's a password
            if (isPassword){
                textField.type = 'text'

            }

            textField.select();
            document.execCommand('copy')

            // Restore the original type if it was a password
            if(isPassword){
                textField.type = 'password'
            }

            // Visual feedback
            const originalText = this.innerHTML
            this.innerHTML = '<i class="fas fa-check"></i> Copied'

            setTimeout(() => {
                this.innerHTML = originalText
            }, 1500)
        })
    })

    // Auto hide the alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');

    alerts.forEach(alert => {
        setTimeout(() =>{
            const bsAlert = new bootstrap.Alert(alert)
            bsAlert.close()
        }, 5000)
    })
})

// Password strength meter
function checkPasswordStrength(password, meterElement, textElement){
    if(!password || !meterElement || !textElement) return;

    let strength =0
    let feedback = ''

    // Check length
    if (password.length >= 12){
        strength += 25
    } else if (password.length >= 8) {
        strength += 15
    }
    // Check for uppercase letters
    if(/[A-Z]/.test(password)){
        strength += 15
    }
    // Check for lowercase letters
    if(/[a-z]/.test(password)){
        strength += 15
    }

    // Check for numbers
    if(/[0-9]/.test(password)){
        strength += 15
    }

    // Check for special characters
    if(/[^A-Za-z0-9]/.test(password)){
        strength += 15
    }

    // Check for repeasted characters
    if (/(.)\1{2,}/.test(password)){
        strength -=10
    }

    // Strength capcity
    strength = Math.min(strength, 100)

    // Set Color and text based on strength
    let color, text

    if(strength < 30){
        color = '#dc3535' // red
        text = 'Weak'
        feedback = 'Your password is weak try adding more character types and making it longer'
    } else if (strength < 60) {
        color = '#ffc107' //yellow
        text = 'Moderate'
        feedback = 'Your password could be stronger. Try adding special characters or making it slightly longer'
    } else if(strength < 80) {
        color = '#28a745';
        text = 'Strong'
        feedback = 'Good and strong password'
    } else {
        color = '#28a745'
        text = 'Very Strong'
        feedback = 'Very strong password'
    }

    // Update meter
    meterElement.style.width = strength + '%'
    meterElement.style.backgroundColor = color

    // Update the text
    textElement.textContent = text + ':' + feedback
    textElement.style.color = color
}

// Function to confirm deletes
function confirmDelete(message, formId){
    if(confirm(message || 'Are you sure you want to delete this item?')){
        document.getElementById(formId).submit()
    }
    return false
}