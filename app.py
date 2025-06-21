import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import os
import logging
from datetime import datetime

# Configuration
MODEL_NAME = "meta-llama/Llama-3.2-1B"
MAX_LENGTH = 512
TEMPERATURE = 0.7

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache the model loading to avoid reloading on every interaction
@st.cache_resource
def load_model():
    """Load the LLM model and tokenizer"""
    try:
        st.info("🔄 Starting model loading process...")
        logger.info(f"Starting to load model: {MODEL_NAME}")
        
        # Load tokenizer
        st.info("📚 Loading tokenizer...")
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        st.success("✅ Tokenizer loaded successfully!")
        logger.info("Tokenizer loaded successfully")
        
        # Add padding token if it doesn't exist
        if tokenizer.pad_token is None:
            st.info("🔧 Configuring tokenizer padding...")
            tokenizer.pad_token = tokenizer.eos_token
            logger.info("Added padding token to tokenizer")
        
        # Load model for CPU inference
        st.info("🧠 Loading language model (this may take several minutes)...")
        st.info("💾 Downloading model files from Hugging Face Hub...")
        logger.info("Starting model download and loading...")
        
        with st.spinner("Downloading and loading model... Please wait..."):
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                torch_dtype=torch.float32,  # Use float32 for CPU
                low_cpu_mem_usage=True,
                device_map="auto"  # Let accelerate handle device mapping automatically
            )
        
        st.success("✅ Language model loaded successfully!")
        logger.info("Model loaded successfully")
        
        # Create pipeline for text generation without specifying device
        st.info("🔗 Creating text generation pipeline...")
        logger.info("Creating text generation pipeline...")
        generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer
            # Remove device parameter to let accelerate handle it
        )
        
        st.success("✅ Pipeline created successfully!")
        logger.info("Text generation pipeline created successfully")
        
        st.success("🎉 Model setup complete! Ready for text generation.")
        logger.info("Model loading process completed successfully")
        
        return generator
    except Exception as e:
        error_msg = f"Error loading model: {str(e)}"
        st.error(error_msg)
        logger.error(error_msg)
        logger.exception("Full error traceback:")
        return None

def generate_completion(generator, prompt, max_length=MAX_LENGTH, temperature=TEMPERATURE):
    """Generate text completion using the loaded model"""
    try:
        logger.info(f"Generating completion for prompt: {prompt[:50]}...")
        
        # Generate text
        result = generator(
            prompt,
            max_length=max_length,
            temperature=temperature,
            do_sample=True,
            pad_token_id=generator.tokenizer.eos_token_id,
            num_return_sequences=1,
            truncation=True
        )
        
        # Extract the generated text (remove the original prompt)
        generated_text = result[0]['generated_text']
        completion = generated_text[len(prompt):].strip()
        
        logger.info(f"Completion generated successfully. Length: {len(completion)} characters")
        return completion
    except Exception as e:
        error_msg = f"Error generating completion: {str(e)}"
        logger.error(error_msg)
        return error_msg

def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="LLM Text Completion App",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Title and description
    st.title("🤖 AI Text Completion App")
    st.markdown("### Powered by Llama-3.2-1B")
    st.markdown("Enter your text prompt below and get AI-generated completions!")
    
    # Sidebar for settings
    st.sidebar.header("⚙️ Settings")
    
    # Model settings
    max_length = st.sidebar.slider(
        "Max Length", 
        min_value=50, 
        max_value=1024, 
        value=MAX_LENGTH, 
        step=50,
        help="Maximum length of generated text"
    )
    
    temperature = st.sidebar.slider(
        "Temperature", 
        min_value=0.1, 
        max_value=2.0, 
        value=TEMPERATURE, 
        step=0.1,
        help="Controls randomness in generation. Higher values = more creative, lower values = more focused"
    )
    
    # Model info
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Model Information:**")
    st.sidebar.markdown(f"- Model: {MODEL_NAME}")
    st.sidebar.markdown("- Device: CPU (Auto-managed)")
    st.sidebar.markdown("- Framework: Hugging Face Transformers")
    
    # Model loading with detailed progress
    st.markdown("---")
    st.subheader("🚀 Model Status")
    
    # Create a placeholder for model loading messages
    model_status_placeholder = st.empty()
    
    with model_status_placeholder.container():
        st.warning("⏳ Initializing model loading...")
        
        # Load model
        generator = load_model()
    
    # Clear the loading messages and show final status
    model_status_placeholder.empty()
    
    if generator is None:
        st.error("❌ Failed to load the model. Please check your internet connection and try again.")
        st.info("💡 **Troubleshooting tips:**")
        st.info("- Ensure you have a stable internet connection")
        st.info("- Check if you have sufficient disk space (5GB+)")
        st.info("- Verify that you have enough RAM (4GB+ available)")
        st.stop()
    
    st.success("✅ Model loaded and ready!")
    
    # Initialize session state for user input
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
    
    st.markdown("---")
    
    # Main interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📝 Input")
        
        # Text input
        user_input = st.text_area(
            "Enter your prompt:",
            value=st.session_state.user_input,
            height=200,
            placeholder="Type your text here... For example: 'The future of artificial intelligence is'"
        )
        
        # Update session state
        st.session_state.user_input = user_input
        
        # Generate button
        generate_button = st.button("🚀 Generate Completion", type="primary")
        
        # Example prompts
        st.markdown("**Example prompts:**")
        example_prompts = [
            "The future of artificial intelligence is",
            "Once upon a time in a distant galaxy,",
            "The benefits of renewable energy include",
            "In the year 2050, technology will",
            "The most important skill for future jobs is"
        ]
        
        for prompt in example_prompts:
            if st.button(f"💡 {prompt}", key=f"example_{prompt}"):
                st.session_state.user_input = prompt
                st.rerun()
    
    with col2:
        st.header("🎯 Output")
        
        if generate_button and user_input.strip():
            with st.spinner("🔄 Generating completion..."):
                # Generate completion
                completion = generate_completion(
                    generator, 
                    user_input, 
                    max_length=max_length, 
                    temperature=temperature
                )
                
                # Display results
                st.markdown("**Generated Completion:**")
                st.text_area(
                    "AI Response:",
                    value=completion,
                    height=200,
                    disabled=True
                )
                
                # Full text
                st.markdown("**Full Text:**")
                full_text = user_input + " " + completion
                st.text_area(
                    "Complete Text:",
                    value=full_text,
                    height=150,
                    disabled=True
                )
                
                # Statistics
                st.markdown("**Statistics:**")
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                
                with col_stats1:
                    st.metric("Input Length", len(user_input.split()))
                
                with col_stats2:
                    st.metric("Generated Length", len(completion.split()))
                
                with col_stats3:
                    st.metric("Total Length", len(full_text.split()))
        
        elif generate_button and not user_input.strip():
            st.warning("Please enter some text before generating completion.")
    
    # Footer
    st.markdown("---")
    st.markdown("**Made with ❤️ by Bhiman using Streamlit and Hugging Face Transformers**")
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

if __name__ == "__main__":
    main() 