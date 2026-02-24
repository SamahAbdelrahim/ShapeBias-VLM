// Single-object description experiment: one video per trial, describe the object.
// Objects 1A through 7E (35 total); only objects with available videos are shown.
document.addEventListener('DOMContentLoaded', function () {
    console.log("Starting object description experiment initialization");
    let timeline = [];

    if (typeof window.logExpData1 !== 'function') {
        console.error("logExpData1 function not available at startup!");
    } else {
        console.log("logExpData1 function verified at startup");
    }

    var jsPsych = initJsPsych({
        use_webaudio: false,
        on_finish: function (data) {
            console.log("Experiment finished, starting data logging");
            var all_trials = jsPsych.data.get().values();
            console.log("Starting to log data");
            console.log(all_trials);

            if (typeof window.logExpData1 !== 'function') {
                console.error("logExpData1 function is not available at experiment end!");
                alert("There was an error saving your data. Please contact the study administrator.");
                return;
            }

            const logPromises = all_trials.map(trial => {
                return new Promise((resolve, reject) => {
                    try {
                        const result = window.logExpData1(trial);
                        if (result instanceof Promise) {
                            result.then(resolve).catch(reject);
                        } else {
                            resolve();
                        }
                    } catch (error) {
                        console.error("Error logging trial:", error);
                        reject(error);
                    }
                });
            });

            Promise.all(logPromises)
                .then(() => {
                    console.log("All data logged successfully, redirecting...");
                    window.location.href = "https://app.prolific.com/submissions/complete?cc=C11U6ZL8";
                })
                .catch(error => {
                    console.error("Failed to log all data:", error);
                    alert("There was an error saving your data. Please contact the study administrator.");
                });
        }
    });

    var globalStyles = `
        <style>
            body {
                font-family: 'Arial', sans-serif;
                background-color: #f9f9f9;
                color: #333;
                text-align: center;
                margin: 0;
                padding: 0;
            }
            .jspsych-display-element {
                max-width: 95%;
                width: 95vw;
                min-width: 800px;
                max-height: 90vh;
                background: white;
                padding: 25px 40px;
                border-radius: 12px;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
                margin: 1vh auto;
                overflow-y: auto;
                overflow-x: hidden;
                position: relative;
                top: 0px;
            }
            .jspsych-btn {
                background-color: #8C1515;
                color: white;
                font-size: 18px;
                padding: 12px 24px;
                border-radius: 8px;
                border: none;
                cursor: pointer;
                transition: 0.3s ease-in-out;
            }
            .jspsych-btn:hover {
                background-color: #700F0F;
            }
            .video-item video {
                width: 100%;
                max-width: 500px;
                height: 350px;
                object-fit: cover;
                border-radius: 8px;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
            }
            @media (max-width: 900px) {
                .video-item video { max-width: 100%; }
            }
        </style>
    `;
    document.head.insertAdjacentHTML('beforeend', globalStyles);

    // Chronological order: 1A, 1B, 1C, 1D, 1E, 2A, 2B, … 7D, 7E (35 total). No shuffle—trials run in this exact order.
    var NUM_OBJECTS = 35;
    var ORDERED_OBJECT_IDS = [
        '1A','1B','1C','1D','1E',
        '2A','2B','2C','2D','2E',
        '3A','3B','3C','3D','3E',
        '4A','4B','4C','4D','4E',
        '5A','5B','5C','5D','5E',
        '6A','6B','6C','6D','6E',
        '7A','7B','7C','7D','7E'
    ];
    var OBJECT_IDS = ORDERED_OBJECT_IDS;

    // Extension used in assets/videos_of_objs/ — use '.mov' or '.mp4' to match your files.
    var VIDEO_EXTENSION = '.mov';

    async function fetchVideoFiles() {
        try {
            console.log("Fetching video files from server...");
            const response = await fetch('/api/videos');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const videoFiles = await response.json();
            console.log(`Found ${videoFiles.length} video files`);
            return videoFiles;
        } catch (error) {
            console.error('Error fetching video files:', error);
            console.log('Live serve / no API: using full list of 35 objects (1A–7E) with extension ' + VIDEO_EXTENSION);
            return OBJECT_IDS.map(function(id) { return id + VIDEO_EXTENSION; });
        }
    }

    async function initializeExperiment() {
        var videoFiles = await fetchVideoFiles();
        var videoSet = {};
        videoFiles.forEach(function(f) { videoSet[f] = true; });

        var objectTrials = OBJECT_IDS.filter(function(id) {
            return videoSet[id + VIDEO_EXTENSION];
        });
        if (objectTrials.length === 0) {
            objectTrials = ORDERED_OBJECT_IDS.slice();
            console.warn('No video list from server; using all 35 objects (1A–7E). Ensure assets/videos_of_objs/ has files named e.g. 1A' + VIDEO_EXTENSION + ', 1B' + VIDEO_EXTENSION + ', ...');
        }
        // Keep chronological order: 1A → 7E. Do not shuffle.
        objectTrials = objectTrials.slice().sort(function(a, b) {
            var na = ORDERED_OBJECT_IDS.indexOf(a);
            var nb = ORDERED_OBJECT_IDS.indexOf(b);
            return (na < 0 ? 999 : na) - (nb < 0 ? 999 : nb);
        });
        window.__objectTrialsOrder = objectTrials;
        window.__assetsBase = (window.ASSETS_BASE || '../assets');
        console.log("Object description trials in chronological order (1A→7E), " + objectTrials.length + " objects:", objectTrials);

        var base = window.__assetsBase;
        var preloadCount = Math.min(5, objectTrials.length);
        for (var p = 0; p < preloadCount; p++) {
            (function(idx) {
                var v = document.createElement('video');
                v.setAttribute('preload', 'auto');
                v.muted = true;
                v.src = base + '/videos_of_objs/' + objectTrials[idx] + VIDEO_EXTENSION;
                v.style.cssText = 'position:absolute;width:0;height:0;opacity:0;pointer-events:none;';
                document.body.appendChild(v);
            })(p);
        }

        var trial1 = {
            type: jsPsychInstructions,
            pages: [
                '<div style="text-align: center; margin-bottom: 10px;"><img src="' + (window.ASSETS_BASE || '../assets') + '/stanford.png"></div>' +
                '<div style="text-align: center; margin: 0 auto; max-width: 600px; font-size: 18px; line-height: 1.5; color: #333;">' +
                '<p>By answering the following questions, you are participating in a study being performed by cognitive scientists in the Stanford Department of Psychology.</p>' +
                '<p>If you have questions about this research, please contact us at <a href="mailto:languagecoglab@gmail.com" style="color: #007bff; text-decoration: none;">languagecoglab@gmail.com</a>.</p>' +
                '<p>You must be at least 18 years old to participate. Your participation in this research is voluntary.</p>' +
                '<p>You may decline to answer any or all of the following questions. You may decline further participation, at any time, without adverse consequences.</p>' +
                '<p>Your anonymity is assured.</p>' +
                '<p><strong>Click "Next" to begin.</strong></p>' +
                '</div>'
            ],
            show_clickable_nav: true,
            button_label: 'Next',
            button_html: '<button class="jspsych-btn" style="font-size: 20px; padding: 12px 24px; background-color: #8C1515; color: white; border: none; border-radius: 10px; cursor: pointer;">%choice%</button>'
        };
        timeline.push(trial1);

        var instructions = {
            type: jsPsychInstructions,
            pages: [
                '<div style="text-align: center; margin: 10px;"></div>' +
                '<div style="text-align: center; margin: 0 auto; max-width: 600px; font-size: 20px; line-height: 1.6; color: #333; padding: 20px;">' +
                '<p style="font-size: 14px; font-weight: bold; background-color: #FFF3CD; padding: 15px; border-radius: 8px; margin: 10px auto; max-width: 500px;">⚠️ You need to view in full screen </p>' +
                '<p>You will see a video of an object. You will be asked to describe the object.</p>' +
                '<p>There will be two hands holding the object—ignore these, and just focus on the object.</p>' +
                '<p>Please click next to begin.</p>' +
                '</div>'
            ],
            on_finish: function (data) {
                var subject_id = jsPsych.data.getURLVariable('PROLIFIC_PID');
                var study_id = jsPsych.data.getURLVariable('STUDY_ID');
                var session_id = jsPsych.data.getURLVariable('SESSION_ID');
                jsPsych.data.addProperties({
                    subject_id: subject_id,
                    study_id: study_id,
                    session_id: session_id,
                });
            },
            show_clickable_nav: true,
            button_label: "Let's Begin",
            button_html: '<button class="jspsych-btn" style="font-size: 20px; padding: 12px 24px; background-color: #8C1515; color: white; border: none; border-radius: 10px; cursor: pointer;">%choice%</button>'
        };
        timeline.push(instructions);

        var main_trials = {
            timeline: [
                {
                    type: jsPsychHtmlButtonResponse,
                    stimulus: function() {
                        var objectId = jsPsych.timelineVariable('object_id');
                        var videoFile = objectId + (typeof VIDEO_EXTENSION !== 'undefined' ? VIDEO_EXTENSION : '.mov');
                        var base = (window.ASSETS_BASE || '../assets');
                        return `
                            <div style="text-align: center; padding: 20px; max-width: 1000px; margin: 0 auto;">
                                <h2 style="font-size: 28px; margin-bottom: 30px; color: #333;">
                                    Describe the object
                                </h2>
                                <div class="video-item" style="margin: 20px auto; position: relative;">
                                    <div id="video-loading-msg" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); font-size: 18px; color: #666;">Loading video…</div>
                                    <video id="obj-video" src="${base}/videos_of_objs/${videoFile}"
                                           preload="auto" playsinline
                                           style="width: 100%; max-width: 500px; height: 350px; object-fit: cover; border-radius: 8px; border: 2px solid #8C1515;"
                                           muted loop>
                                    </video>
                                </div>
                                <p id="instruction-text" style="margin-top: 25px; font-size: 18px; color: #666; max-width: 600px; margin-left: auto; margin-right: auto;">
                                    Please watch the video, then describe the object in the box below.
                                </p>
                                <div style="margin-top: 25px; max-width: 700px; margin-left: auto; margin-right: auto;">
                                    <textarea id="description-text"
                                              placeholder="Type your description here..."
                                              style="width: 100%; height: 140px; padding: 15px; border: 2px solid #8C1515; border-radius: 8px; font-size: 16px; font-family: Arial, sans-serif; resize: vertical; box-sizing: border-box;"
                                              required></textarea>
                                </div>
                                <div style="margin-top: 20px;">
                                    <button id="desc-continue-btn" class="jspsych-btn" style="font-size: 18px; padding: 15px 30px; background-color: #8C1515; color: white; border: none; border-radius: 8px; cursor: pointer; min-width: 200px;">Continue</button>
                                </div>
                            </div>
                        `;
                    },
                    choices: [],
                    on_load: function() {
                        var video = document.getElementById('obj-video');
                        var loadingMsg = document.getElementById('video-loading-msg');
                        var LOAD_TIMEOUT_MS = 2000;

                        function hideLoadingAndPlay() {
                            if (loadingMsg) loadingMsg.style.display = 'none';
                            if (video) video.play().catch(function(e) { console.error("Error playing video:", e); });
                        }

                        if (video) {
                            if (video.readyState >= 2) {
                                hideLoadingAndPlay();
                            } else {
                                var done = false;
                                function onReady() {
                                    if (done) return;
                                    done = true;
                                    hideLoadingAndPlay();
                                }
                                video.addEventListener('canplay', onReady, { once: true });
                                video.addEventListener('loadeddata', onReady, { once: true });
                                video.addEventListener('error', function() {
                                    if (done) return;
                                    done = true;
                                    if (loadingMsg) loadingMsg.textContent = 'Video failed to load.';
                                }, { once: true });
                                setTimeout(function() {
                                    if (!done) {
                                        done = true;
                                        hideLoadingAndPlay();
                                    }
                                }, LOAD_TIMEOUT_MS);
                            }
                        } else if (loadingMsg) {
                            loadingMsg.textContent = 'Video element not found.';
                        }

                        var order = window.__objectTrialsOrder;
                        var base = window.__assetsBase;
                        if (order && base) {
                            var currentId = jsPsych.timelineVariable('object_id');
                            var currentIdx = order.indexOf(currentId);
                            var nextId = currentIdx >= 0 && currentIdx + 1 < order.length ? order[currentIdx + 1] : null;
                            if (nextId) {
                                var nextSrc = base + '/videos_of_objs/' + nextId + VIDEO_EXTENSION;
                                if (!window.__preloadVideo) {
                                    window.__preloadVideo = document.createElement('video');
                                    window.__preloadVideo.setAttribute('preload', 'auto');
                                    window.__preloadVideo.muted = true;
                                    document.body.appendChild(window.__preloadVideo);
                                    window.__preloadVideo.style.cssText = 'position:absolute;width:0;height:0;opacity:0;pointer-events:none;';
                                }
                                window.__preloadVideo.src = nextSrc;
                            }
                        }

                        var btn = document.getElementById('desc-continue-btn');
                        var textarea = document.getElementById('description-text');
                        if (btn && textarea) {
                            btn.addEventListener('click', function() {
                                if (!textarea.value.trim()) {
                                    alert('Please provide a description before continuing.');
                                    return;
                                }
                                window.currentDescriptionValue = textarea.value.trim();
                                jsPsych.finishTrial();
                            });
                        }
                    },
                    on_finish: function(data) {
                        var objectId = jsPsych.timelineVariable('object_id');
                        var description = window.currentDescriptionValue || '';
                        window.currentDescriptionValue = '';
                        jsPsych.data.addDataToLastTrial({
                            object_id: objectId,
                            video_file: objectId + (typeof VIDEO_EXTENSION !== 'undefined' ? VIDEO_EXTENSION : '.mov'),
                            explanation: description,
                            trial_type: "description_trial",
                            block: "main_experiment"
                        });
                    }
                }
            ],
            timeline_variables: objectTrials.map(function(id) { return { object_id: id }; }),
            randomize_order: false
        };
        timeline.push(main_trials);

        var goodbye = {
            type: jsPsychInstructions,
            pages: [
                '<div style="text-align: center; margin: 50px;"><img src="' + (window.ASSETS_BASE || '../assets') + '/stanford.png"></div>' +
                '<div style="text-align: center; margin: 0 auto; max-width: 600px; font-size: 30px;">' +
                '<p> <b>Thank you for your participation and we appreciate you helping science. </b> </p>' +
                '<p> Please click next to get redirected ...  </p>' +
                '</div>'
            ],
            show_clickable_nav: true,
        };
        timeline.push(goodbye);

        jsPsych.run(timeline);
    }

    initializeExperiment().catch(function(error) {
        console.error('Error initializing experiment:', error);
        alert('Error loading experiment. Please refresh the page and try again.');
    });
});
