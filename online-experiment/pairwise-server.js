require('dotenv').config();
const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const port = process.env.PORT || 3020;

// Optional MongoDB (for local simulation without DB)
let mongoose, ComplexityPairwiseVid, mongoConnected = false;
const mongoAuthPath = path.join(__dirname, 'mongo_auth.json');
if (fs.existsSync(mongoAuthPath)) {
    try {
        mongoose = require('mongoose');
        ComplexityPairwiseVid = require('./assets/variables/variables-pairwise-logger.js');
        const raw_data = fs.readFileSync(mongoAuthPath);
        const auth = JSON.parse(raw_data);
        const mongoDBUri = `mongodb://${auth.user}:${auth.password}@127.0.0.1:27017/samah?authSource=admin`;
        mongoose.connect(mongoDBUri)
            .then(() => { mongoConnected = true; console.log('Connected to MongoDB...'); })
            .catch(err => console.error('Could not connect to MongoDB (logs will only go to console):', err.message));
    } catch (e) {
        console.warn('MongoDB not used:', e.message);
    }
}

// Middleware to parse JSON
app.use(express.json());

// Serve assets at /general_assets and /assets (relative paths from experiment_scripts/experiment.html use ../assets -> /assets when page is at /)
app.use('/general_assets', express.static(path.join(__dirname, 'assets')));
app.use('/assets', express.static(path.join(__dirname, 'assets')));
// Serve experiment_scripts for direct access to experiment_scripts/experiment.html
app.use('/experiment_scripts', express.static(path.join(__dirname, 'experiment_scripts')));

// Experiment page: redirect so URL is /experiment_scripts/experiment.html and relative paths (../assets, experiment_open_ended.js) resolve
app.get('/', (req, res) => res.redirect('/experiment_scripts/experiment.html'));

// API endpoint to get video files from assets/videos_of_objs
app.get('/api/videos', (req, res) => {
    try {
        const videosDir = path.join(__dirname, 'assets', 'videos_of_objs');
        const files = fs.readdirSync(videosDir);
        const videoFiles = files.filter(file => {
            const ext = path.extname(file).toLowerCase();
            return ['.mp4', '.mov', '.avi', '.mkv', '.webm'].includes(ext);
        });
        console.log(`Found ${videoFiles.length} video files`);
        res.json(videoFiles);
    } catch (error) {
        console.error('Error reading videos directory:', error);
        res.status(500).json({ error: 'Failed to read videos directory' });
    }
});

// Logging (saves to MongoDB when connected, otherwise logs to console)
app.post('/api/log', (req, res) => {
    try {
        console.log('Log:', JSON.stringify(req.body, null, 2));
    } catch (e) {
        console.error('Error in POST request:', e);
    }
    const { rt, trial_type, trial_index, time_elapsed, internal_node_id, subject, response, pic, stimulus, block, study_id, session_id, video1, video2, chosen_video, chosen_object, explanation, leftVideo, rightVideo, leftObject, rightObject, left_video, right_video } = req.body;

    if (mongoConnected && ComplexityPairwiseVid) {
        const newLog = new ComplexityPairwiseVid({ rt, trial_type, trial_index, time_elapsed, internal_node_id, subject, response, pic, stimulus, block, study_id, session_id, video1, video2, chosen_video, chosen_object, explanation, leftVideo, rightVideo, leftObject, rightObject, left_video, right_video });
        newLog.save()
            .then(() => res.send('Action logged successfully'))
            .catch(err => res.status(500).send('Error logging action: ' + err.message));
    } else {
        res.send('Action logged (console only)');
    }
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
    console.log('Open http://localhost:' + port + ' to run the experiment.');
});
