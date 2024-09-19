import { streamGemini } from './gemini-api.js';

let form = document.getElementById('chatForm');
let promptInput = document.querySelector('input[name="prompt"]');
// let output = document.querySelector('.output');
let output = document.getElementById('chatHistory');

const chatHistory = document.getElementById('chatHistory');

form.onsubmit = async (ev) => {
    const chatButtons = document.getElementById('suggestedPrompts');
    if (chatButtons) {
        chatButtons.remove();
    }

    const welcomeSign = document.getElementById('welcomeSign');
    if (welcomeSign) {
        welcomeSign.remove();
    }

    const fileName = document.getElementById('fileName');
    const fileIcon = document.getElementById('fileIcon');
    if (fileName.textContent != '' && fileName.textContent != 'File upload failed.') {
        fileName.className = 'd-none bg-white';
        fileIcon.className = 'd-none bg-white';
        let file_name = fileName.textContent;
        fileName.textContent = '';

        // New user chat of the file
        const newFileChat = document.createElement('div'); // Create a new <div> element
        newFileChat.className = "d-flex align-items-baseline mb-4 text-end justify-content-end"; // Add a class
        newFileChat.style = "padding-left: 400px; padding-right: 300px;"
        newFileChat.innerHTML =`<div class="pe-2">
                                    <div class="card d-inline-block p-2 px-3 m-1"></div>
                                </div>`;
        const cardElement = newFileChat.querySelector('.card'); // Target the element with class 'card'
        cardElement.textContent = '📁' + file_name; // Replace the text
        chatHistory.appendChild(newFileChat);
    }

    if (promptInput.value.trim() != "") {
        // USER CHAT
        const newUserChat = document.createElement('div'); // Create a new <div> element
        newUserChat.className = "d-flex align-items-baseline mb-4 text-end justify-content-end"; // Add a class
        newUserChat.style = "padding-left: 400px; padding-right: 300px;"
        newUserChat.innerHTML =`<div class="pe-2">
                                    <div class="card d-inline-block p-2 px-3 m-1"></div>
                                </div>`;

        const cardElement = newUserChat.querySelector('.card'); // Target the element with class 'card'
        cardElement.textContent = promptInput.value; // Replace the text

        // document.body.appendChild(newUserChat);
        chatHistory.appendChild(newUserChat);
    }

    // NEW BOT CHAT
    const newBotChat = document.createElement('div'); // Create a new <div> element
    newBotChat.className = "d-flex align-items-baseline mb-4"; // Add a class
    newBotChat.style = "padding-left: 300px; padding-right: 400px;"
    newBotChat.innerHTML =`<div class="pe-2">
                                <div class="card d-inline-block p-2 px-3 m-1"></div>
                            </div>`;

    const cardBotElement = newBotChat.querySelector('.card'); // Target the element with class 'card'
    output = cardBotElement; // Replace the text

    // document.body.appendChild(newBotChat);
    chatHistory.appendChild(newBotChat);

    ev.preventDefault();
    output.textContent = 'Generating...';

    try {
        // Load the image as a base64 string
        

        // Assemble the prompt by combining the text with the chosen image
        let contents = [
        {
            type: "text",
            text: promptInput.value,
        }
        ];

        promptInput.value = ""

        // Call the gemini-pro-vision model, and get a stream of results
        let stream = streamGemini({
        model: 'gemini-pro',
        contents,
        });

        // Read from the stream and interpret the output as markdown
        let buffer = [];
        let md = new markdownit();
        for await (let chunk of stream) {
        buffer.push(chunk);
        output.innerHTML = md.render(buffer.join(''));
        }
    } catch (e) {
        output.innerHTML += '<hr>' + e;
    }

    const feedbackButtons = document.createElement('div'); // Create a new <div> element
    feedbackButtons.className = "d-flex justify-content-left mt-1";
    feedbackButtons.style = "padding-left: 300px; padding-right: 400px;"
    feedbackButtons.innerHTML = `<button type="button" class="btn btn-outline-primary btn-sm mx-1" id="goodButton">Good response</button>
                                <button type="button" class="btn btn-outline-danger btn-sm mx-1" id="badButton">Bad response</button>`
    chatHistory.appendChild(feedbackButtons);
    const goodButton = feedbackButtons.querySelector('#goodButton');
    const badButton = feedbackButtons.querySelector('#badButton');
    console.log("HEYYY")
    goodButton.addEventListener('click', function() {
        console.log('Good response button clicked');
        pendo.track('Feedback Clicked', { feedback: 'Good' });
        goodButton.disabled = true;
        badButton.disabled = true;
    });
    badButton.addEventListener('click', function() {
        console.log('Bad response button clicked');
        pendo.track('Feedback Clicked', { feedback: 'Bad' });
        goodButton.disabled = true;
        badButton.disabled = true;
    });
    console.log("BEYYYYY")
};

document.addEventListener('DOMContentLoaded', () => {
    // Get references to the buttons
    const prompt1Button = document.getElementById('prompt1');
    const prompt2Button = document.getElementById('prompt2');
    const prompt3Button = document.getElementById('prompt3');

    const submitButton = document.getElementById('submitButton');
    
    // Get reference to the prompt input box
    const promptInput = document.querySelector('input[name="prompt"]');
    
    // Add event listeners to the buttons
    prompt1Button.addEventListener('click', () => {
      promptInput.value = 'Explain the basic elements of [legal concept]';
      submitButton.disabled = false;
    });
    
    prompt2Button.addEventListener('click', () => {
      promptInput.value = 'Can you review this [type of document] and identify any potential issues?';
      submitButton.disabled = false;
    });
    
    prompt3Button.addEventListener('click', () => {
      promptInput.value = 'Can you find relevant case law on [topic] in [jurisdiction]?';
      submitButton.disabled = false;
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chatInput');
    const fileName = document.getElementById('fileName');
    const submitButton = document.getElementById('submitButton');

    function updateButtonState() {
        const isTextInputEmpty = chatInput.value.trim() === '';
        const isDivEmpty = fileName.textContent.trim() === '';
        submitButton.disabled = isTextInputEmpty && isDivEmpty;
    }

    chatInput.addEventListener('input', updateButtonState);

    const observer = new MutationObserver(updateButtonState);
    observer.observe(fileName, { childList: true, subtree: true });
});

