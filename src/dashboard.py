# src/dashboard.py - FIXED VERSION
import gradio as gr
from typing import Optional, Callable
from loguru import logger

def create_dashboard(get_service: Callable):
    """Create Gradio dashboard interface with lazy service loading"""
    
    def get_sentiment_service():
        """Get sentiment service instance (lazy loading)"""
        service = get_service()
        if service is None:
            return None
        return service
    
    def predict_gradio(text: str) -> str:
        """Gradio prediction function"""
        if not text or not text.strip():
            return "⚠️ Please enter some text to analyze."
        
        try:
            service = get_sentiment_service()
            if service is None:
                return "❌ Service not initialized. Please try again in a moment."
            
            import asyncio
            result = asyncio.run(service.analyze_single(text))
            
            # Create formatted response
            emoji = "✅" if result.label == "POSITIVE" else "❌"
            confidence = result.score * 100
            
            return f"""{emoji} **{result.label}**

**Confidence:** {confidence:.1f}%
**Processing:** {result.processing_time_ms:.1f}ms
**Cached:** {'Yes' if result.cached else 'No'}
"""
        except Exception as e:
            logger.error(f"Gradio prediction error: {e}")
            return f"❌ Error: {str(e)}"
    
    def update_stats():
        """Update cache statistics"""
        try:
            service = get_sentiment_service()
            if service is None:
                return "⏳ Service initializing..."
            
            stats = service.get_cache_stats()
            return f"""
📊 **Cache Statistics**

**Size:** {stats['size']} items
**Hits:** {stats['hits']:,}
**Misses:** {stats['misses']:,}
**Hit Rate:** {stats['hit_rate']:.2%}
**Total Requests:** {stats['total_requests']:,}
"""
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return f"❌ Error loading stats: {str(e)}"
    
    def process_batch(texts: str) -> str:
        """Process batch of texts"""
        lines = [t.strip() for t in texts.split('\n') if t.strip()]
        if not lines:
            return "⚠️ Please enter at least one text."
        
        try:
            service = get_sentiment_service()
            if service is None:
                return "❌ Service not initialized. Please try again in a moment."
            
            import asyncio
            results = asyncio.run(service.analyze_batch(lines))
            
            output = "📦 **Batch Results:**\n\n"
            for i, r in enumerate(results, 1):
                emoji = "✅" if r.label == "POSITIVE" else "❌"
                output += f"{i}. {emoji} **{r.label}** ({r.score:.2%}) - {r.text[:50]}{'...' if len(r.text) > 50 else ''}\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Batch error: {e}")
            return f"❌ Batch processing failed: {str(e)}"
    
    # Create interface
    with gr.Blocks(title="Sentiment Analysis Dashboard", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎯 Sentiment Analysis Dashboard

        Analyze text sentiment using the production-grade API backend.

        **Features:**
        - Real-time sentiment prediction
        - Confidence scores with percentages
        - Caching for performance
        - Batch processing support
        - Cache statistics monitoring
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.Textbox(
                    lines=3,
                    placeholder="Enter text to analyze... (e.g., 'I love this product!')",
                    label="Input Text",
                    show_label=True
                )
                
                submit_btn = gr.Button("🔮 Analyze", variant="primary", size="lg")
                
                with gr.Accordion("📦 Batch Processing", open=False):
                    batch_input = gr.Textbox(
                        lines=3,
                        placeholder="Enter multiple texts (one per line)...\nExample:\nGreat product!\nTerrible service\nIt's okay",
                        label="Batch Input"
                    )
                    batch_btn = gr.Button("📊 Analyze Batch", variant="secondary")
            
            with gr.Column(scale=1):
                output_text = gr.Textbox(
                    label="Analysis Result",
                    interactive=False,
                    lines=10
                )
                
                # Stats
                with gr.Accordion("📈 Performance Stats", open=True):
                    stats_text = gr.Textbox(
                        label="Cache Statistics",
                        interactive=False,
                        lines=6
                    )
                    refresh_stats_btn = gr.Button("🔄 Refresh Stats", size="sm")
        
        # Event handlers
        submit_btn.click(
            fn=predict_gradio,
            inputs=text_input,
            outputs=output_text
        )
        
        text_input.submit(
            fn=predict_gradio,
            inputs=text_input,
            outputs=output_text
        )
        
        refresh_stats_btn.click(
            fn=update_stats,
            outputs=stats_text
        )
        
        batch_btn.click(
            fn=process_batch,
            inputs=batch_input,
            outputs=output_text
        )
        
        # Load stats on page load with retry
        def load_initial_stats():
            import time
            for attempt in range(5):
                stats = update_stats()
                if "initializing" not in stats:
                    return stats
                time.sleep(1)
            return "⏳ Service still initializing. Please refresh in a moment."
        
        demo.load(fn=load_initial_stats, outputs=stats_text)
    
    logger.info("✅ Gradio dashboard created")
    return demo