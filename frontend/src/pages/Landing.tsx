import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Chrome } from "lucide-react";

const Landing = () => {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate("/application");
  };

  return (
    <div className="min-h-screen bg-gradient-background flex items-center justify-center p-6">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 left-1/4 w-64 h-64 bg-primary/20 rounded-full blur-3xl"></div>
      </div>

      {/* Main content */}
      <div className="relative z-10 w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-primary rounded-xl mb-4">
            <Chrome className="w-6 h-6 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">RePrice</h1>
          <p className="text-muted-foreground">Your intelligent pricing companion</p>
        </div>

        {/* Login Form */}
        <div className="bg-card/50 backdrop-blur-xl border border-border rounded-2xl p-8 shadow-card animate-fade-in">
          <h2 className="text-2xl font-semibold text-foreground text-center mb-8">
            Log into your account
          </h2>

          <div className="space-y-4">
            {/* Primary CTA Button */}
            <Button 
              onClick={handleGetStarted}
              size="lg" 
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-medium h-12 rounded-xl shadow-glow transition-all duration-300 hover:shadow-lg hover:scale-[1.02]"
            >
              <Chrome className="w-5 h-5 mr-2" />
              Login with Google
            </Button>
          </div>

          <div className="mt-8 text-center">
            <p className="text-muted-foreground text-sm">
              Don't have an account?{" "}
              <button className="text-primary hover:text-primary/80 font-medium transition-colors">
                Sign up
              </button>
            </p>
          </div>

          <div className="mt-6 text-center text-xs text-muted-foreground">
            By continuing, you agree to our{" "}
            <button className="underline hover:text-foreground transition-colors">
              Terms of Service
            </button>{" "}
            and{" "}
            <button className="underline hover:text-foreground transition-colors">
              Privacy Policy
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Landing;