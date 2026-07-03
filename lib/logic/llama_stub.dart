/// Stub for llama_cpp when FFI is not available (web)
/// This allows the app to compile for web with graceful degradation

class LlamaProcessor {
  LlamaProcessor(String path, ContextParams params) {
    throw UnsupportedError('LlamaProcessor requires native FFI support');
  }
  
  Stream<String> stream(String prompt) async* {
    throw UnsupportedError('LlamaProcessor requires native FFI support');
  }
  
  void unload() {
    // No-op
  }
}

class ContextParams {
  final String model;
  final int ctx;
  final int threads;
  
  const ContextParams({
    required this.model,
    required this.ctx,
    required this.threads,
  });
}
