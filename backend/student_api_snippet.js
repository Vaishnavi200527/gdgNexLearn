const studentAPI = {
    // --- Assignment Endpoints ---
    // Matches backend/routers/student.py: @router.get("/assignments")
    getAssignments: async () => {
        return await apiRequest('/student/assignments');
    },

    // Matches backend/routers/student.py: @router.get("/assignments/{id}")
    getAssignment: async (id) => {
        return await apiRequest(`/student/assignments/${id}`);
    },

    // Matches backend/routers/student.py: @router.post("/assignments/{id}/submit")
    submitAssignment: async (id, data) => {
        return await apiRequest(`/student/assignments/${id}/submit`, 'POST', data);
    },

    // --- Quiz Endpoints ---
    // Matches backend/routers/quiz.py: @router.get("/student")
    getQuizzes: async () => {
        return await apiRequest('/api/quizzes/student');
    },

    // Matches backend/routers/quiz.py: @router.get("/{quiz_id}")
    getQuiz: async (id) => {
        return await apiRequest(`/api/quizzes/${id}`);
    },

    // Matches backend/routers/quiz.py: @router.post("/{quiz_id}/submit")
    submitQuiz: async (id, data) => {
        return await apiRequest(`/api/quizzes/${id}/submit`, 'POST', data);
    }
};