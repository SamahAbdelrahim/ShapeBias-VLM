// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function () {
    console.log("Starting pairwise comparison experiment initialization");
    let timeline = [];

    // Verify logExpData1 is available at startup
    if (typeof window.logExpData1 !== 'function') {
        console.error("logExpData1 function not available at startup!");
    } else {
        console.log("logExpData1 function verified at startup");
    }

    var jsPsych = initJsPsych({
        use_webaudio: false,
        on_finish: function (data) {
            console.log("Experiment finished, starting data logging");
            //jsPsych.data.displayData();

            var all_trials = jsPsych.data.get().values();
            console.log("Starting to log data");
            console.log(all_trials);

            // Check if logExpData1 is available
            if (typeof window.logExpData1 !== 'function') {
                console.error("logExpData1 function is not available at experiment end!");
                alert("There was an error saving your data. Please contact the study administrator.");
                return;
            }

            // Log each trial individually with error handling
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

            // Handle all logging promises
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
            /* General Page Styling */
            body {
                font-family: 'Arial', sans-serif;
                background-color: #f9f9f9;
                color: #333;
                text-align: center;
                margin: 0;
                padding: 0;
            }
        
            /* Main Content Box */
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
        
            /* Improve Button Styles */
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

            /* Video comparison layout */
            .video-comparison-container {
                display: flex;
                justify-content: space-around;
                align-items: center;
                margin: 20px 0;
                gap: 40px;
            }

            .video-item {
                flex: 1;
                max-width: 400px;
                text-align: center;
            }

            .video-item video {
                width: 100%;
                max-width: 350px;
                height: 250px;
                object-fit: cover;
                border-radius: 8px;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
            }

            .video-label {
                font-size: 18px;
                font-weight: bold;
                margin: 10px 0;
                color: #333;
            }

            .comparison-buttons {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-top: 30px;
            }

            .comparison-btn {
                background-color: #8C1515;
                color: white;
                font-size: 16px;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                transition: 0.3s ease-in-out;
                min-width: 120px;
            }

            .comparison-btn:hover {
                background-color: #700F0F;
                transform: translateY(-2px);
            }

            .comparison-btn:disabled {
                background-color: #ccc;
                cursor: not-allowed;
                transform: none;
            }

            /* Responsive design */
            @media (max-width: 900px) {
                .video-comparison-container {
                    flex-direction: column;
                    gap: 20px;
                }
                
                .video-item {
                    max-width: 100%;
                }
            }
        </style>
    `;
    
    // Inject global styles into the page
    document.head.insertAdjacentHTML('beforeend', globalStyles);

    // Function to fetch video files dynamically from the server
    async function fetchVideoFiles() {
        try {
            console.log("Fetching video files from server...");
            // Use relative path - this will work whether running locally or on the server
            const response = await fetch('/api/videos');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const videoFiles = await response.json();
            console.log(`Found ${videoFiles.length} video files:`, videoFiles);
            return videoFiles;
        } catch (error) {
            console.error('Error fetching video files:', error);
            console.log('Falling back to default video list...');
            // Fallback to a smaller set if API fails
            return [
                "File 2.mp4", "File 3.mp4", "File 4.mp4", "File 5.mp4", "File 6.mp4",
                "File 7.mp4", "File 8.mp4", "File 9.mp4", "File 10.mp4"
            ];
        }
    }

    // Initialize videos array (will be populated asynchronously)
    let videos = [];

    // Function to shuffle an array using Fisher-Yates algorithm
    function shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }

    // Function to generate all possible pairwise combinations with position counterbalancing
    function generatePairwiseCombinations(videoList) {
        let combinations = [];
        for (let i = 0; i < videoList.length; i++) {
            for (let j = i + 1; j < videoList.length; j++) {
                // Randomly decide which video goes on left vs right
                if (Math.random() < 0.5) {
                    combinations.push({
                        video1: videoList[i],
                        video2: videoList[j],
                        left_video: videoList[i],
                        right_video: videoList[j]
                    });
                } else {
                    combinations.push({
                        video1: videoList[j],
                        video2: videoList[i],
                        left_video: videoList[j],
                        right_video: videoList[i]
                    });
                }
            }
        }
        return shuffleArray(combinations);
    }

    // Main async function to initialize the experiment
    async function initializeExperiment() {
        // Fetch videos from server
        videos = await fetchVideoFiles();
        console.log("Videos loaded:", videos);

        // Generate pairwise combinations
        let pairwiseTrials1 = generatePairwiseCombinations(videos);
        console.log("Generated pairwise trials:", pairwiseTrials1);

        const pairwiseTrials = pairwiseTrials1.slice(0, 10);
        console.log("pairwiseTrials", pairwiseTrials);

        // Welcome and consent
        var trial1 = {
            type: jsPsychInstructions,
        pages: [
            '<div style="text-align: center; margin-bottom: 10px;"><img src="/general_assets/stanford.png"></div>' +
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

        // Experiment instructions
        var instructions = {
            type: jsPsychInstructions,
        pages: [
            '<div style="text-align: center; margin: 10px;"></div>' +
            '<div style="text-align: center; margin: 0 auto; max-width: 600px; font-size: 20px; line-height: 1.6; color: #333; padding: 20px;">' +
            '<p style="font-size: 14px; font-weight: bold; background-color: #FFF3CD; padding: 15px; border-radius: 8px; margin: 10px auto; max-width: 500px;">⚠️ You need to view in full screen </p>' +
            '<p>In this experiment, you will see pairs of videos showing objects being inspected by a human.</p>' +
            '<p>For each pair, you will be asked to decide which object appears more <strong>complex</strong>.</p>' +
            '<p>Use your intuition to make these judgments - there are no right or wrong answers.</p>' +
            '<p>After you have made your choice, you will be asked to explain your choice.</p>' +
            '<p>Please click next to begin.</p>' +
            '</div>'
        ],
        on_finish: function (data) {
            // Capture info from Prolific
            var subject_id = jsPsych.data.getURLVariable('PROLIFIC_PID');
            var study_id = jsPsych.data.getURLVariable('STUDY_ID');
            var session_id = jsPsych.data.getURLVariable('SESSION_ID');

            console.log("subject");
            console.log(subject_id);

            jsPsych.data.addProperties({
                subject_id: subject_id,
                study_id: study_id,
                session_id: session_id,
            });

            console.log("from object data");
            console.log(data.subject_id, data.study_id, data.session_id);
        },
        show_clickable_nav: true,
        button_label: "Let's Begin",
        button_html: '<button class="jspsych-btn" style="font-size: 20px; padding: 12px 24px; background-color: #8C1515; color: white; border: none; border-radius: 10px; cursor: pointer;">%choice%</button>'
    };

        timeline.push(instructions);


        // Main experiment trials - Video comparison with integrated open-ended question
        var main_trials = {
            timeline: [
            {
                type: jsPsychHtmlButtonResponse,
                stimulus: function() {
                    var leftVideo = jsPsych.timelineVariable('left_video');
                    var rightVideo = jsPsych.timelineVariable('right_video');
                    
                    return `
                        <div style="text-align: center; padding: 20px; max-width: 1000px; margin: 0 auto;">
                            <h2 style="font-size: 28px; margin-bottom: 40px; color: #333;">
                                Which object is more complex?
                            </h2>
                            
                            <div style="display: flex; justify-content: center; align-items: flex-start; gap: 60px; margin: 40px 0;">
                                <div style="text-align: center;">
                                    <div style="font-size: 20px; font-weight: bold; margin-bottom: 15px; color: #8C1515;">Object A</div>
                                    <video id="video1" src="/general_assets/videos_familiarobjs/${leftVideo}" 
                                           style="width: 350px; height: 250px; object-fit: cover; border-radius: 8px; border: 2px solid #8C1515;"
                                           muted loop>
                                    </video>
                                </div>
                                
                                <div style="text-align: center;">
                                    <div style="font-size: 20px; font-weight: bold; margin-bottom: 15px; color: #8C1515;">Object B</div>
                                    <video id="video2" src="/general_assets/videos_familiarobjs/${rightVideo}" 
                                           style="width: 350px; height: 250px; object-fit: cover; border-radius: 8px; border: 2px solid #8C1515;"
                                           muted loop>
                                    </video>
                                </div>
                            </div>
                            
                            <p id="instruction-text" style="margin-top: 30px; font-size: 18px; color: #666; max-width: 600px; margin-left: auto; margin-right: auto;">
                                Please wait for both videos to finish playing before making your choice.
                            </p>
                            
                            <div id="explanation-section" style="display: none; margin-top: 30px;">
                                <h3 style="font-size: 22px; margin-bottom: 20px; color: #333;">Please explain your choice:</h3>
                                <textarea id="explanation-text" 
                                          placeholder="Type your explanation here..." 
                                          style="width: 80%; max-width: 600px; height: 120px; padding: 15px; border: 2px solid #8C1515; border-radius: 8px; font-size: 16px; font-family: Arial, sans-serif; resize: vertical;"
                                          required></textarea>
                                <br><br>
                                <button id="submit-explanation" class="jspsych-btn" style="font-size: 18px; padding: 15px 30px; background-color: #8C1515; color: white; border: none; border-radius: 8px; cursor: pointer; min-width: 200px;">
                                    Continue
                                </button>
                            </div>
                        </div>
                    `;
                },
                choices: ['Object A is more complex', 'Object B is more complex'],
                button_html: '<button class="jspsych-btn" style="font-size: 18px; padding: 15px 30px; margin: 15px; background-color: #8C1515; color: white; border: none; border-radius: 8px; cursor: pointer; min-width: 200px;">%choice%</button>',
                on_load: function() {
                    var video1 = document.getElementById('video1');
                    var video2 = document.getElementById('video2');
                    var instructionText = document.getElementById('instruction-text');
                    var explanationSection = document.getElementById('explanation-section');
                    var submitButton = document.getElementById('submit-explanation');
                    
                    // Hide buttons initially
                    var buttons = document.querySelectorAll('.jspsych-btn');
                    buttons.forEach(btn => btn.style.display = 'none');
                    
                    // Track if each video has completed its first play
                    let video1Completed = false;
                    let video2Completed = false;

                    console.log("Setting up video completion tracking");
                    
                    // Log video properties
                    console.log("Video1 properties:", {
                        duration: video1.duration,
                        readyState: video1.readyState,
                        paused: video1.paused,
                        src: video1.src
                    });
                    console.log("Video2 properties:", {
                        duration: video2.duration,
                        readyState: video2.readyState,
                        paused: video2.paused,
                        src: video2.src
                    });

                    // Add loadedmetadata event listeners
                    video1.addEventListener('loadedmetadata', function() {
                        console.log("Video1 metadata loaded - Duration:", video1.duration);
                    });

                    video2.addEventListener('loadedmetadata', function() {
                        console.log("Video2 metadata loaded - Duration:", video2.duration);
                    });

                    // Add play event listeners
                    video1.addEventListener('play', function() {
                        console.log("Video1 started playing");
                    });

                    video2.addEventListener('play', function() {
                        console.log("Video2 started playing");
                    });

                    // Start both videos with error handling
                    Promise.all([
                        video1.play().catch(error => console.error("Error playing video1:", error)),
                        video2.play().catch(error => console.error("Error playing video2:", error))
                    ]).then(() => {
                        console.log("Both videos started playing");
                    });

                    // Function to check if both videos have completed their first play
                    function checkBothVideosCompleted() {
                        console.log("Checking completion - Video1:", video1Completed, "Video2:", video2Completed);
                        if (video1Completed && video2Completed) {
                            console.log("Both videos completed, showing buttons");
                            buttons.forEach(btn => {
                                btn.style.display = 'inline-block';
                                console.log("Button display style set to:", btn.style.display);
                            });
                            instructionText.style.color = '#333';
                            instructionText.style.fontWeight = 'bold';
                        }
                    }

                    // Add timeupdate event listeners to check when videos reach their end
                    video1.addEventListener('timeupdate', function() {
                        if (!video1Completed && video1.currentTime >= video1.duration * 0.9) {  // Check at 90% of duration
                            console.log("Video1 reached end - Duration:", video1.duration, "Current time:", video1.currentTime);
                            video1Completed = true;
                            checkBothVideosCompleted();
                        }
                    });

                    video2.addEventListener('timeupdate', function() {
                        if (!video2Completed && video2.currentTime >= video2.duration * 0.9) {  // Check at 90% of duration
                            console.log("Video2 reached end - Duration:", video2.duration, "Current time:", video2.currentTime);
                            video2Completed = true;
                            checkBothVideosCompleted();
                        }
                    });

                    // Also check completion on the 'ended' event as a backup
                    video1.addEventListener('ended', function() {
                        if (!video1Completed) {
                            console.log("Video1 ended event fired");
                            video1Completed = true;
                            checkBothVideosCompleted();
                        }
                    });

                    video2.addEventListener('ended', function() {
                        if (!video2Completed) {
                            console.log("Video2 ended event fired");
                            video2Completed = true;
                            checkBothVideosCompleted();
                        }
                    });

                    // Add a fallback timer to check completion after a reasonable time
                    setTimeout(function() {
                        if (!video1Completed && video1.duration && video1.currentTime >= video1.duration * 0.8) {
                            console.log("Video1 fallback completion check");
                            video1Completed = true;
                            checkBothVideosCompleted();
                        }
                        if (!video2Completed && video2.duration && video2.currentTime >= video2.duration * 0.8) {
                            console.log("Video2 fallback completion check");
                            video2Completed = true;
                            checkBothVideosCompleted();
                        }
                    }, 1000); // Check after 1 second
                    
                    // Handle choice button clicks
                    buttons.forEach(btn => {
                        btn.addEventListener('click', function() {
                            // Hide choice buttons
                            buttons.forEach(b => b.style.display = 'none');
                            
                            // Show explanation section
                            explanationSection.style.display = 'block';
                            
                            // Update instruction text
                            instructionText.textContent = 'Please explain why you made this choice. What made the object appear complex?';
                            instructionText.style.color = '#333';
                            instructionText.style.fontWeight = 'bold';
                        });
                    });
                    
                    // Handle submit explanation button
                    if (submitButton) {
                        submitButton.addEventListener('click', function() {
                            var explanationText = document.getElementById('explanation-text');
                            if (explanationText && explanationText.value.trim() !== '') {
                                // Continue to next trial
                                jsPsych.finishTrial();
                            } else {
                                alert('Please provide an explanation before continuing.');
                            }
                        });
                    }
                },
                on_finish: function(data) {
                    var leftVideo = jsPsych.timelineVariable('left_video');
                    var rightVideo = jsPsych.timelineVariable('right_video');

                    console.log("trial data:", data);

                    jsPsych.data.addDataToLastTrial({
                        leftVideo: leftVideo,
                        rightVideo: rightVideo,
                        chosen_video: data.response === 0 ? leftVideo : rightVideo,
                        chosen_position: data.response === 0 ? 'left' : 'right',
                        chosen_object: data.response === 0 ? 'Object A' : 'Object B',
                        trial_type: "comparison_trial",
                        block: "main_experiment"
                    });
                }
            },
            {
                type: jsPsychHtmlButtonResponse,
                stimulus: function() {
                    var leftVideo = jsPsych.timelineVariable('left_video');
                    var rightVideo = jsPsych.timelineVariable('right_video');
                    var chosenObject = jsPsych.data.get().last(1).values()[0].chosen_object;
                    var chosenVideo = jsPsych.data.get().last(1).values()[0].chosen_video;
                    
                    // Determine which video was chosen for highlighting
                    var isLeftVideoChosen = chosenObject === 'Object A';
                    var leftVideoBorder = isLeftVideoChosen ? '4px solid #28a745' : '2px solid #8C1515';
                    var rightVideoBorder = !isLeftVideoChosen ? '4px solid #28a745' : '2px solid #8C1515';
                    var leftVideoLabel = isLeftVideoChosen ? 'Object A (Your Choice)' : 'Object A';
                    var rightVideoLabel = !isLeftVideoChosen ? 'Object B (Your Choice)' : 'Object B';
                    
                    return `
                        <div style="text-align: center; padding: 20px; max-width: 1000px; margin: 0 auto;">
                            <h2 style="font-size: 28px; margin-bottom: 40px; color: #333;">
                                Explain Your Choice
                            </h2>
                            
                            <div style="display: flex; justify-content: center; align-items: flex-start; gap: 60px; margin: 40px 0;">
                                <div style="text-align: center;">
                                    <div style="font-size: 20px; font-weight: bold; margin-bottom: 15px; color: ${isLeftVideoChosen ? '#28a745' : '#8C1515'};">${leftVideoLabel}</div>
                                    <video id="video1" src="/general_assets/videos_familiarobjs/${leftVideo}" 
                                           style="width: 350px; height: 250px; object-fit: cover; border-radius: 8px; border: ${leftVideoBorder};"
                                           muted autoplay loop>
                                    </video>
                                </div>
                                
                                <div style="text-align: center;">
                                    <div style="font-size: 20px; font-weight: bold; margin-bottom: 15px; color: ${!isLeftVideoChosen ? '#28a745' : '#8C1515'};">${rightVideoLabel}</div>
                                    <video id="video2" src="/general_assets/videos_familiarobjs/${rightVideo}" 
                                           style="width: 350px; height: 250px; object-fit: cover; border-radius: 8px; border: ${rightVideoBorder};"
                                           muted autoplay loop>
                                    </video>
                                </div>
                            </div>
                            
                            <div style="margin-top: 40px; max-width: 800px; margin-left: auto; margin-right: auto;">
                                <h3 style="font-size: 22px; margin-bottom: 20px; color: #333;">
                                    Please explain why you chose ${chosenObject} as more complex:
                                </h3>
                                <textarea id="explanation-text" 
                                          placeholder="Type your explanation here..." 
                                          style="width: 100%; height: 150px; padding: 20px; border: 2px solid #8C1515; border-radius: 8px; font-size: 16px; font-family: Arial, sans-serif; resize: vertical; box-sizing: border-box;"
                                          required></textarea>
                            </div>
                        </div>
                    `;
                },
                choices: ['Continue'],
                button_html: '<button class="jspsych-btn" style="font-size: 18px; padding: 15px 30px; margin: 15px; background-color: #8C1515; color: white; border: none; border-radius: 8px; cursor: pointer; min-width: 200px;">%choice%</button>',
                on_load: function() {
                    // Start both videos
                    var video1 = document.getElementById('video1');
                    var video2 = document.getElementById('video2');
                    if (video1) video1.play();
                    if (video2) video2.play();
                    
                    // Add validation to the continue button
                    var continueButton = document.querySelector('.jspsych-btn');
                    if (continueButton) {
                        continueButton.addEventListener('click', function(e) {
                            var explanationText = document.getElementById('explanation-text');
                            if (!explanationText || explanationText.value.trim() === '') {
                                e.preventDefault();
                                e.stopPropagation();
                                alert('Please provide an explanation before continuing.');
                                return false;
                            } else {
                                // Store the explanation value before the trial finishes
                                window.currentExplanationValue = explanationText.value;
                            }
                        });
                    }
                },
                on_finish: function(data) {
                    // Get the explanation text from the stored value
                    var explanation = window.currentExplanationValue || '';
                    console.log("explanation", explanation);
                    var leftVideo = jsPsych.timelineVariable('left_video');
                    var rightVideo = jsPsych.timelineVariable('right_video');
                    var chosenVideo = jsPsych.data.get().last(1).values()[0].chosen_video;
                    var chosenObject = jsPsych.data.get().last(1).values()[0].chosen_object;
                    
                    // Store the explanation in this trial's data
                    jsPsych.data.addDataToLastTrial({
                        leftVideo: leftVideo,
                        rightVideo: rightVideo,
                        chosen_video: chosenVideo,
                        chosen_object: chosenObject,
                        explanation: explanation,
                        trial_type: "explanation_trial"
                    });
                    
                    // Clear the stored value
                    window.currentExplanationValue = '';
                }
            }
        ],
        timeline_variables: pairwiseTrials, // Use all combinations for main experiment
        randomize_order: true
    };

        timeline.push(main_trials);

        // Thank you message
        var goodbye = {
            type: jsPsychInstructions,
        pages: [
            '<div style="text-align: center; margin: 50px;"><img src="/general_assets/stanford.png"></div>' +
            '<div style="text-align: center; margin: 0 auto; max-width: 600px; font-size: 30px;">' +
            '<p> <b>Thank you for your participation and we appreciate you helping science. </b> </p>' +
            '<p> please click next to get redirected ...  </p>' +
            '</div>'
        ],
        show_clickable_nav: true,
    };

        timeline.push(goodbye);

        // Run the timeline
        jsPsych.run(timeline);
    }

    // Start the experiment by calling the async function
    initializeExperiment().catch(error => {
        console.error('Error initializing experiment:', error);
        alert('Error loading experiment. Please refresh the page and try again.');
    });
}); 