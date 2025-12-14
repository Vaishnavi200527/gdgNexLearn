import { apiService } from './apiService.js';

class TeacherAPI {
    constructor(apiService) {
        this.api = apiService;
    }

    async createQuiz(quizData) {
        return this.api.request('/api/quizzes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(quizData)
        });
    }

    async assignQuizToClass(quizId, classId, dueDate) {
        return this.api.request('/api/quizzes/assign', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                quiz_id: quizId,
                class_id: classId,
                due_date: dueDate
            })
        });
    }

    async getClasses() {
        return this.api.request('/api/teacher/classes', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
    }

    async getQuizzes() {
        return this.api.request('/api/teacher/quizzes', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
    }

    async getQuiz(quizId) {
        return this.api.request(`/api/teacher/quizzes/${quizId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
    }

    async updateQuiz(quizId, quizData) {
        return this.api.request(`/api/teacher/quizzes/${quizId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(quizData)
        });
    }

    async getQuizSubmissions(quizId) {
        return this.api.request(`/api/teacher/quizzes/${quizId}/submissions`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
    }
}

// Create and export a singleton instance
export const teacherAPI = new TeacherAPI(apiService);
