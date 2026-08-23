import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an unhandled rendering error:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 rounded-3xl bg-slate-900 border border-amber-500/30 text-slate-200 text-center space-y-4 my-6 animate-fade-in">
          <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mx-auto text-2xl">
            ⚠️
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-100">
              {this.props.fallbackTitle || 'Unable to render this workspace view.'}
            </h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              {this.state.error?.message || 'A temporary rendering error occurred.'}
            </p>
          </div>
          <button
            onClick={this.handleReset}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl transition-all shadow-md"
          >
            🔄 Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
