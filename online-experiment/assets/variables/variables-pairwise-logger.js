const mongoose = require('mongoose');
console.log("variables-pairwise-logger.js loaded");
// Define the schema for "complexity pairwise Video Logs" collection
const complexityPairwiseVidSchema = new mongoose.Schema({
    rt: Number,
    trial_type: String,
    trial_index: Number,
    time_elapsed: Number,
    internal_node_id: Number,
    subject: String,
    response: String,
    pic: String,
    stimulus: String,
    block: String,
    study_id: String,
    session_id: String,
    video1: String,
    video2: String,
    chosen_video: String,
    chosen_object: String,
    explanation: String,
    leftVideo: String,
    rightVideo: String,
    leftObject: String,
    rightObject: String,
    left_video: String,
    right_video: String,


});

// Create the model for "complexitylogs" collection
const ComplexityPairwiseVid = mongoose.model('complexityPairwiseVid', complexityPairwiseVidSchema);

module.exports = ComplexityPairwiseVid;
