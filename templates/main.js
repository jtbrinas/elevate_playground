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
};

document.addEventListener('DOMContentLoaded', () => {
    // Get references to the buttons
    const prompt1Button = document.getElementById('prompt1');
    const prompt2Button = document.getElementById('prompt2');
    const prompt3Button = document.getElementById('prompt3');
    
    // Get reference to the prompt input box
    const promptInput = document.querySelector('input[name="prompt"]');
    
    // Add event listeners to the buttons
    prompt1Button.addEventListener('click', () => {
      promptInput.value = 'List important legal concepts and explain the basic elements of the one that I choose';
    });
    
    prompt2Button.addEventListener('click', () => {
      promptInput.value = 'Can you review this [type of document] and identify any potential issues?';
    });
    
    prompt3Button.addEventListener('click', () => {
      promptInput.value = 'Can you find relevant case law on [topic] in [jurisdiction]?';
    });

});

