// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    if (tabs.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Get the tab's target content
                const target = tab.getAttribute('data-target');
                
                // Remove active class from all tabs and contents
                tabs.forEach(t => t.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked tab and its content
                tab.classList.add('active');
                document.getElementById(target).classList.add('active');
            });
        });
    }
    
    // Rating selection for feedback
    const ratingOptions = document.querySelectorAll('.rating-option input');
    if (ratingOptions.length > 0) {
        ratingOptions.forEach(option => {
            option.addEventListener('change', function() {
                document.querySelector('input[name="rating"]').value = this.value;
            });
        });
    }
    
    // Calendar functionality for reservation
    const calendarDays = document.querySelectorAll('.calendar-day');
    const selectedDateInput = document.getElementById('selected-date');
    
    if (calendarDays.length > 0 && selectedDateInput) {
        calendarDays.forEach(day => {
            day.addEventListener('click', function() {
                // Remove selected class from all days
                calendarDays.forEach(d => d.classList.remove('selected'));
                
                // Add selected class to clicked day
                this.classList.add('selected');
                
                // Update the hidden input value
                selectedDateInput.value = this.getAttribute('data-date');
                
                // Update the displayed selected date
                document.getElementById('selected-date-display').textContent = this.getAttribute('data-date');
            });
        });
    }
    
    // Handle laboratory selection in feedback form
    const labSelect = document.getElementById('laboratory-select');
    if (labSelect) {
        labSelect.addEventListener('change', function() {
            document.querySelector('input[name="laboratory"]').value = this.value;
        });
    }
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('invalid');
                    
                    // Create error message if it doesn't exist
                    let errorMsg = field.nextElementSibling;
                    if (!errorMsg || !errorMsg.classList.contains('error-message')) {
                        errorMsg = document.createElement('div');
                        errorMsg.classList.add('error-message');
                        errorMsg.style.color = 'red';
                        errorMsg.style.fontSize = '12px';
                        errorMsg.style.marginTop = '5px';
                        field.parentNode.insertBefore(errorMsg, field.nextSibling);
                    }
                    errorMsg.textContent = 'This field is required';
                } else {
                    field.classList.remove('invalid');
                    const errorMsg = field.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('error-message')) {
                        errorMsg.textContent = '';
                    }
                }
            });
            
            if (!isValid) {
                event.preventDefault();
            }
        });
    });
    
    // Reservation form handling
    const purposeSelect = document.getElementById('purpose-select');
    const laboratorySelect = document.getElementById('laboratory-select');
    const timeSlotSelect = document.getElementById('time-slot-select');
    const selectedPurposeDisplay = document.getElementById('selected-purpose');
    const selectedLabDisplay = document.getElementById('selected-laboratory');
    const selectedTimeDisplay = document.getElementById('selected-time');
    
    if (purposeSelect && selectedPurposeDisplay) {
        purposeSelect.addEventListener('change', function() {
            selectedPurposeDisplay.textContent = this.value;
            document.querySelector('input[name="purpose"]').value = this.value;
        });
    }
    
    if (laboratorySelect && selectedLabDisplay) {
        laboratorySelect.addEventListener('change', function() {
            selectedLabDisplay.textContent = this.value;
            document.querySelector('input[name="laboratory"]').value = this.value;
        });
    }
    
    if (timeSlotSelect && selectedTimeDisplay) {
        timeSlotSelect.addEventListener('change', function() {
            selectedTimeDisplay.textContent = this.value;
            document.querySelector('input[name="time_slot"]').value = this.value;
        });
    }
    
    // Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            setTimeout(() => {
                message.style.opacity = '0';
                setTimeout(() => {
                    message.style.display = 'none';
                }, 500);
            }, 5000);
        });
    }
});
