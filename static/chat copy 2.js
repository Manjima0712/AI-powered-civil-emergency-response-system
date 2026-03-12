let socket;

let mediaRecorder;
let audioChunks = [];



let username= document.getElementById("u_name").textContent;
if (username){

    initializeChat();
}


function initializeChat() {
    socket = io();
   
    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('chat_history', (messages) => {
        const messagesDiv = document.getElementById('messages');
        messagesDiv.innerHTML = '';
        messages.forEach(displayMessage);
    });

    socket.on('new_message', displayMessage);

    socket.on('message_deleted', (data) => {
        const messageElement = document.getElementById(data.messageId);
        if (messageElement) {
            messageElement.remove();
        }
    });

    document.getElementById('message-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    document.getElementById('send-button').addEventListener('click', sendMessage);
    document.getElementById('file-button').addEventListener('click', () => {
        document.getElementById('file-input').click();
    });

    document.getElementById('file-input').addEventListener('change', uploadFile);
    document.getElementById('voice-button').addEventListener('click', toggleVoiceRecording);
    document.getElementById('location-button').addEventListener('click', shareLocation);
}

function getFileType(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const imageTypes = ['jpg', 'jpeg', 'png', 'gif', 'bmp'];
    const videoTypes = ['mp4', 'webm', 'ogg'];
   
    if (imageTypes.includes(ext)) return 'image';
    if (videoTypes.includes(ext)) return 'video';
    return 'other';
}

function showImageModal(src) {
    const imageModal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    modalImage.src = src;
    imageModal.style.display = "block";
}

function displayMessage(message) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.id = message.id;
    messageDiv.className = `message ${message.user === username ? 'message-own' : 'message-other'}`;

    let content = '';
    if (message.type === 'text') {
        content = `<div>${message.text}</div>`;
    } else if (message.type === 'file') {
        const fileType = getFileType(message.originalFilename);
        if (fileType === 'image') {
            content = `
                <div class="media-content">
                    <img src="/uploads/${message.filename}" alt="Image" onclick="showImageModal('/uploads/${message.filename}')">
                </div>`;
        } else if (fileType === 'video') {
            content = `
                <div class="media-content">
                    <video controls>
                        <source src="/uploads/${message.filename}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                </div>`;
        } else {
            content = `<div><a href="/uploads/${message.filename}" target="_blank">${message.originalFilename}</a></div>`;
        }
    } else if (message.type === 'voice') {
        content = `
            <div>
                <audio controls class="audio">
                    <source src="/uploads/${message.filename}" type="audio/wav">
                </audio>
            </div>`;
    } else if (message.type === 'location') {
        content = `
            <div>
                <a href="https://www.google.com/maps?q=${message.latitude},${message.longitude}" target="_blank">
                    View Location
                </a>
            </div>`;
    }

    messageDiv.innerHTML = `
        ${content}
        <div class="timestamp">
            ${message.user} - ${message.timestamp}
            ${message.user === username ?
                `<button class="btn btn-sm btn-link delete" onclick="deleteMessage('${message.id}')">
                    <i class="fas fa-trash" style="font-size: 12px; color:red;"></i>
                </button>` : ''}
        </div>`;

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
   
    if (message) {
        socket.emit('send_message', {
            username: username,
            message: message
        });
        input.value = '';
    }
}

function uploadFile(event) {
    const file = event.target.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('username', username);

        fetch('/upload_file', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            socket.emit('send_file', data);
        });
       
        // Reset file input
        event.target.value = '';
    }
}

function toggleVoiceRecording() {
    const voiceButton = document.getElementById('voice-button');
    
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });

                mediaRecorder.addEventListener('stop', () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const formData = new FormData();
                    formData.append('voice', audioBlob, 'voice.wav');
                    formData.append('username', username);

                    // Stop all tracks in the stream
                    stream.getTracks().forEach(track => track.stop());

                    fetch('/upload_voice', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => {
                        if (!response.ok) throw new Error('Upload failed');
                        return response.json();
                    })
                    .then(data => {
                        socket.emit('send_voice', {
                            username: username,
                            filename: data.filename,
                            originalFilename: 'voice.wav'
                        });
                    })
                    .catch(error => {
                        console.error('Error uploading voice:', error);
                        alert('Failed to upload voice recording. Please try again.');
                    })
                    .finally(() => {
                        voiceButton.classList.remove('btn-danger');
                    });
                });

                mediaRecorder.start();
                voiceButton.classList.add('btn-danger');
                
                // Auto-stop after 60 seconds
                setTimeout(() => {
                    if (mediaRecorder && mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                    }
                }, 60000);
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                alert('Unable to access microphone. Please check your browser permissions.');
                voiceButton.classList.remove('btn-danger');
            });
    } else {
        mediaRecorder.stop();
        voiceButton.classList.remove('btn-danger');
    }
}


function shareLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            socket.emit('send_location', {
                username: username,
                latitude: position.coords.latitude,
                longitude: position.coords.longitude
            });
        });
    }
}

function deleteMessage(messageId) {
    socket.emit('delete_message', { messageId: messageId });
}
const chatIcon = document.getElementById('chat-icon');
const chatBox = document.getElementById('chat');

chatIcon.addEventListener('click', () => {
    if (chatBox.style.display === 'none' || chatBox.style.display === '') {
        chatBox.style.display = 'flex';
    } else {
        chatBox.style.display = 'none';
    }
});