import { studentAPI } from '../src/services/api.js';

document.addEventListener('DOMContentLoaded', () => {
    const quizContainer = document.getElementById('quiz-container');
    const questionsContainer = document.getElementById('questions-container');
    const submitButton = document.getElementById('submit-quiz');
    const resultContainer = document.getElementById('result-container');
    const scoreElement = document.getElementById('score');
    const quizTitleElement = document.getElementById('quiz-title');

    const urlParams = new URLSearchParams(window.location.search);
    const quizId = urlParams.get('id');

    if (!quizId) {
        quizContainer.innerHTML = '<p class="text-red-500">Quiz ID not found in URL.</p>';
        return;
    }

    let quizData;

    studentAPI.getQuizById(quizId)
        .then(quiz => {
            quizData = quiz;
            quizTitleElement.textContent = quiz.title;
            renderQuestions(quiz.questions);
        })
        .catch(error => {
            questionsContainer.innerHTML = `<p class="text-red-500">Error loading quiz: ${error.message}</p>`;
        });

    function renderQuestions(questions) {
        questions.forEach((question, index) => {
            const questionElement = document.createElement('div');
            questionElement.classList.add('mb-8');
            questionElement.innerHTML = `
                <p class="text-xl font-semibold mb-4">${index + 1}. ${question.question_text}</p>
                <div class="flex flex-col gap-2">
                    ${Object.entries(question.options).map(([key, value]) => `
                        <label class="flex items-center gap-x-3 bg-gray-800 p-4 rounded-lg hover:bg-gray-700 cursor-pointer">
                            <input type="radio" name="question-${question.id}" value="${key}" class="form-radio h-5 w-5 text-primary bg-gray-900 border-gray-700 focus:ring-primary">
                            <span class="text-white">${value}</span>
                        </label>
                    `).join('')}
                </div>
            `;
            questionsContainer.appendChild(questionElement);
        });
    }

    submitButton.addEventListener('click', () => {
        const answers = {};
        quizData.questions.forEach(question => {
            const selectedOption = document.querySelector(`input[name="question-${question.id}"]:checked`);
            if (selectedOption) {
                answers[question.id] = selectedOption.value;
            }
        });

        studentAPI.submitQuiz(quizId, answers)
            .then(result => {
                quizContainer.classList.add('hidden');
                resultContainer.classList.remove('hidden');
                scoreElement.textContent = `${result.score.toFixed(2)}%`;
            })
            .catch(error => {
                alert(`Error submitting quiz: ${error.message}`);
            });
    });
});
