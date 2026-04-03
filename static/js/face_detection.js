/**
 * Face detection logic using face-api.js
 * Requires face-api.js loaded via CDN
 */

const FaceDetector = {
    video: null,
    canvas: null,
    overlayCanvas: null,
    isDetecting: false,
    modelsLoaded: false,
    onFaceDetected: null, 
    onFaceLost: null,
    minConfidence: 0.5,
    drawBoxes: true,
    
    // Model URLs
    MODEL_URL: 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model',

    async init(videoElement, overlayCanvasElement) {
        this.video = videoElement;
        this.overlayCanvas = overlayCanvasElement;
        
        // Wait for faceapi to load
        if (typeof faceapi === 'undefined') {
            console.error("faceapi is not defined. Ensure face-api.js is loaded.");
            return false;
        }

        try {
            console.log("Loading face detection models...");
            await faceapi.nets.tinyFaceDetector.loadFromUri(this.MODEL_URL);
            await faceapi.nets.faceLandmark68Net.loadFromUri(this.MODEL_URL);
            console.log("Face models loaded successfully.");
            this.modelsLoaded = true;
            return true;
        } catch (error) {
            console.error("Error loading face models:", error);
            return false;
        }
    },

    startDetection(callback) {
        if (!this.modelsLoaded || !this.video || this.isDetecting) return;
        
        this.onFaceDetected = callback;
        this.isDetecting = true;
        
        // Ensure overlay canvas matches video size
        if (this.overlayCanvas) {
            this.overlayCanvas.width = this.video.clientWidth || this.video.videoWidth;
            this.overlayCanvas.height = this.video.clientHeight || this.video.videoHeight;
        }

        this.detectLoop();
    },

    stopDetection() {
        this.isDetecting = false;
        if (this.overlayCanvas) {
            const ctx = this.overlayCanvas.getContext('2d');
            ctx.clearRect(0, 0, this.overlayCanvas.width, this.overlayCanvas.height);
        }
    },

    async detectLoop() {
        if (!this.isDetecting) return;

        if (this.video.paused || this.video.ended) {
            setTimeout(() => this.detectLoop(), 100);
            return;
        }

        try {
            const options = new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: this.minConfidence });
            
            const result = await faceapi.detectSingleFace(this.video, options).withFaceLandmarks();

            // Handle overlay sizing and drawing
            if (this.overlayCanvas && this.drawBoxes) {
                const displaySize = { 
                    width: this.video.clientWidth || this.video.videoWidth, 
                    height: this.video.clientHeight || this.video.videoHeight 
                };
                
                if (displaySize.width > 0 && displaySize.height > 0) {
                    this.overlayCanvas.width = displaySize.width;
                    this.overlayCanvas.height = displaySize.height;
                    faceapi.matchDimensions(this.overlayCanvas, displaySize);
                    
                    const ctx = this.overlayCanvas.getContext('2d');
                    ctx.clearRect(0, 0, this.overlayCanvas.width, this.overlayCanvas.height);

                    if (result) {
                        const resizedDetections = faceapi.resizeResults(result, displaySize);
                        
                        // Custom drawing logic instead of faceapi.draw.drawDetections for better styling
                        const box = resizedDetections.detection.box;
                        ctx.strokeStyle = 'rgba(0, 210, 255, 0.7)';
                        ctx.lineWidth = 2;
                        
                        // Draw corners
                        const cornerLength = 20;
                        ctx.beginPath();
                        // Top-left
                        ctx.moveTo(box.x, box.y + cornerLength);
                        ctx.lineTo(box.x, box.y);
                        ctx.lineTo(box.x + cornerLength, box.y);
                        // Top-right
                        ctx.moveTo(box.x + box.width - cornerLength, box.y);
                        ctx.lineTo(box.x + box.width, box.y);
                        ctx.lineTo(box.x + box.width, box.y + cornerLength);
                        // Bottom-right
                        ctx.moveTo(box.x + box.width, box.y + box.height - cornerLength);
                        ctx.lineTo(box.x + box.width, box.y + box.height);
                        ctx.lineTo(box.x + box.width - cornerLength, box.y + box.height);
                        // Bottom-left
                        ctx.moveTo(box.x + cornerLength, box.y + box.height);
                        ctx.lineTo(box.x, box.y + box.height);
                        ctx.lineTo(box.x, box.y + box.height - cornerLength);
                        ctx.stroke();
                        
                        //faceapi.draw.drawFaceLandmarks(this.overlayCanvas, resizedDetections);
                    }
                }
            }

            if (result) {
                const analysis = this.analyzeFace(result);
                if (this.onFaceDetected) {
                    this.onFaceDetected(result, analysis);
                }
            } else {
                if (this.onFaceLost) {
                    this.onFaceLost();
                }
            }
        } catch (error) {
            console.error("Detection error:", error);
        }

        // Loop using requestAnimationFrame for better performance
        if (this.isDetecting) {
            requestAnimationFrame(() => this.detectLoop());
            // setTimeout(() => this.detectLoop(), 100);
        }
    },

    analyzeFace(detectionResult) {
        const box = detectionResult.detection.box;
        const landmarks = detectionResult.landmarks;
        
        // Video dimensions
        const vw = this.video.videoWidth || 640;
        const vh = this.video.videoHeight || 480;

        // Position analysis (0.0 to 1.0)
        const centerX = (box.x + (box.width / 2)) / vw;
        const centerY = (box.y + (box.height / 2)) / vh;
        
        // Size analysis
        const faceRatio = (box.width * box.height) / (vw * vh);
        
        // Yaw / pitch estimation from landmarks
        // Nose tip is point 30. Left edge is 0, right edge is 16.
        const nosePoint = landmarks.getNose()[3]; // 30
        const leftPoint = landmarks.getJawOutline()[0]; // 0
        const rightPoint = landmarks.getJawOutline()[16]; // 16
        
        // Simple yaw estimate (ratio of left-nose vs nose-right distance)
        const leftToNose = nosePoint.x - leftPoint.x;
        const noseToRight = rightPoint.x - nosePoint.x;
        const yawRatio = leftToNose / (noseToRight + 0.001); // 1.0 is forward, < 0.8 is right, > 1.2 is left
        
        let pose = 'front';
        if (yawRatio > 1.5) pose = 'left';
        else if (yawRatio < 0.66) pose = 'right';
        // Basic pitch based on nose vs eye level
        
        return {
            centerX,
            centerY,
            faceRatio,
            pose,
            isCentered: centerX > 0.3 && centerX < 0.7 && centerY > 0.2 && centerY < 0.8,
            isGoodSize: faceRatio > 0.05 && faceRatio < 0.4
        };
    }
};

window.FaceDetector = FaceDetector;
