document.addEventListener('DOMContentLoaded', () => {
    const sosButton = document.getElementById('sosButton');
    const countdownContainer = document.getElementById('countdownContainer');
    const countdownDisplay = document.getElementById('countdown');
    const cancelButton = document.getElementById('cancelButton');
    const contactForm = document.getElementById('contactForm');
    const contactList = document.getElementById('contactList');

    let countdownTimer;
    let contacts = [];

    // Function to validate phone number
    function validatePhoneNumber(phone) {
        const phoneRegex = /^[+]?[\d\s()-]{10,15}$/;
        return phoneRegex.test(phone);
    }

    // Function to add contact
    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('contactName').value.trim();
        const phone = document.getElementById('contactPhone').value.trim();

        if (!name || !validatePhoneNumber(phone)) {
            alert('Please enter a valid name and phone number');
            return;
        }

        try {
            const response = await fetch('/add_contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, phone })
            });

            const result = await response.json();

            if (response.ok) {
                renderContacts();
                contactForm.reset();
                alert('Contact added successfully!');
            } else {
                alert(result.error || 'Failed to add contact');
            }
        } catch (error) {
            console.error('Error adding contact:', error);
            alert('Network error. Could not add contact.');
        }
    });

    // Function to render contacts
    async function renderContacts() {
        try {
            const response = await fetch('/get_contacts');
            contacts = await response.json();
            
            if (contacts.length === 0) {
                contactList.innerHTML = '<p class="text-center text-muted">No contacts added yet</p>';
                return;
            }
            
            contactList.innerHTML = contacts.map(contact => `
                <div class="contact-item d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                    <div>
                        <strong>${contact.name}</strong>
                        <small class="text-muted d-block">${contact.phone}</small>
                    </div>
                    <button class="btn btn-sm btn-danger" onclick="deleteContact(${contact.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error fetching contacts:', error);
            contactList.innerHTML = '<p class="text-center text-danger">Failed to load contacts</p>';
        }
    }

    // Function to delete contact
    window.deleteContact = async (contactId) => {
        const confirmDelete = confirm('Are you sure you want to delete this contact?');
        
        if (!confirmDelete) return;

        try {
            const response = await fetch(`/delete_contact/${contactId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                renderContacts();
                alert('Contact deleted successfully');
            } else {
                alert('Failed to delete contact');
            }
        } catch (error) {
            console.error('Error deleting contact:', error);
            alert('Network error. Could not delete contact.');
        }
    };

    // SOS Countdown Functionality
    window.startSOS = () => {
        if (contacts.length === 0) {
            alert('Please add emergency contacts first');
            return;
        }

        let countdown = 10;
        sosButton.disabled = true;
        countdownContainer.style.display = 'block';

        countdownTimer = setInterval(() => {
            countdownDisplay.textContent = countdown;
            
            if (countdown <= 0) {
                clearInterval(countdownTimer);
                sendEmergencySMS();
                countdownContainer.style.display = 'none';
                sosButton.disabled = false;
            }
            
            countdown--;
        }, 1000);
    };

    // Cancel SOS Countdown
    window.cancelSOS = () => {
        clearInterval(countdownTimer);
        countdownContainer.style.display = 'none';
        sosButton.disabled = false;
        countdownDisplay.textContent = '';
    };

    // Function to send emergency SMS
    async function sendEmergencySMS() {
        try {
            const response = await fetch('/send_emergency_sms', {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                let message = 'Emergency Alert Sent!\n\n';
                
                if (data.successful_contacts && data.successful_contacts.length > 0) {
                    message += `Sent successfully to:\n${data.successful_contacts.join(', ')}\n\n`;
                }
                
                if (data.failed_contacts && data.failed_contacts.length > 0) {
                    message += `Failed to send to:\n${data.failed_contacts.join(', ')}`;
                }

                alert(message);
            } else {
                alert(`Failed to send emergency SMS: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error sending emergency SMS:', error);
            alert('Network error. Could not send emergency SMS.');
        }
    }

    // Initial setup
    function init() {
        renderContacts();
    }

    // Initialize the application
    init();
});


C:\Users\USER\Desktop\emergency\emergency\web\static\