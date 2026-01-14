// PDF Viewer JavaScript
const pdfjsLib = window.pdfjsLib;
const studentAPI = window.studentAPI;

// Global variables
let pdfDoc = null;
let currentPage = 1;
let scale = 1.0;
let assignment = null;
let pdfUrl = '';

// DOM elements
const canvas = document.getElementById('pdfCanvas');
const ctx = canvas.getContext('2d');
const loadingOverlay = document.getElementById('loadingOverlay');
const pageInfo = document.getElementById('pageInfo');
const prevPageBtn = document.getElementById('prevPage');
const nextPageBtn = document.getElementById('nextPage');
const zoomInBtn = document.getElementById('zoomIn');
const zoomOutBtn = document.getElementById('zoomOut');
const zoomLevel = document.getElementById('zoomLevel');
const downloadBtn = document.getElementById('downloadBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadAssignment();
    setupEventListeners();
});

// Load assignment
async function loadAssignment() {
    const urlParams = new URLSearchParams(window.location.search);
    const assignmentId = urlParams.get('id');
    if (!assignmentId) {
        alert('Assignment ID not found');
        return;
    }

    try {
        assignment = await studentAPI.getAssignmentById(assignmentId);
        document.getElementById('assignmentTitle').textContent = assignment.title;
        document.getElementById('infoTitle').textContent = assignment.title;
        document.getElementById('infoDescription').textContent = assignment.description;
        // Add more assignment details as needed

        pdfUrl = assignment.content_url.startsWith('http') ? assignment.content_url : `http://localhost:8000${assignment.content_url}`;
        const loadingTask = pdfjsLib.getDocument(pdfUrl);
        pdfDoc = await loadingTask.promise;
        renderPage(currentPage);
        pageInfo.textContent = `${currentPage} / ${pdfDoc.numPages}`;
        loadingOverlay.style.display = 'none';
    } catch (error) {
        console.error('Error loading PDF:', error);
        alert('Failed to load PDF');
    }
}

// Render page
function renderPage(pageNum) {
    pdfDoc.getPage(pageNum).then(function(page) {
        const viewport = page.getViewport({scale: scale});
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        const renderContext = {
            canvasContext: ctx,
            viewport: viewport
        };
        page.render(renderContext);
    });
}

// Setup event listeners
function setupEventListeners() {
    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderPage(currentPage);
            pageInfo.textContent = `${currentPage} / ${pdfDoc.numPages}`;
        }
    });

    nextPageBtn.addEventListener('click', () => {
        if (currentPage < pdfDoc.numPages) {
            currentPage++;
            renderPage(currentPage);
            pageInfo.textContent = `${currentPage} / ${pdfDoc.numPages}`;
        }
    });

    zoomInBtn.addEventListener('click', () => {
        scale += 0.25;
        renderPage(currentPage);
        zoomLevel.textContent = `${Math.round(scale * 100)}%`;
    });

    zoomOutBtn.addEventListener('click', () => {
        if (scale > 0.5) {
            scale -= 0.25;
            renderPage(currentPage);
            zoomLevel.textContent = `${Math.round(scale * 100)}%`;
        }
    });

    downloadBtn.addEventListener('click', async (event) => {
        const downloadBtn = event.target.closest('button');
        const originalText = downloadBtn.innerHTML;
        downloadBtn.innerHTML = 'Downloading...';
        downloadBtn.disabled = true;
        try {
            const response = await fetch(pdfUrl);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = assignment ? `${assignment.title}.pdf` : 'assignment.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Error downloading PDF:', error);
            alert('Failed to download PDF. Please try again.');
        } finally {
            downloadBtn.innerHTML = originalText;
            downloadBtn.disabled = false;
        }
    });

    // Add event listeners for other buttons like markCompleteBtn, startQuizBtn, etc.
    const markCompleteBtn = document.getElementById('markCompleteBtn');
    if (markCompleteBtn) {
        markCompleteBtn.addEventListener('click', () => {
            // Implement mark as complete functionality
            alert('Assignment marked as complete!');
        });
    }

    const startQuizBtn = document.getElementById('startQuizBtn');
    if (startQuizBtn) {
        startQuizBtn.addEventListener('click', () => {
            // Implement start quiz functionality
            alert('Starting quiz...');
        });
    }
}
