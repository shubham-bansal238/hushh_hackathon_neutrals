import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Chrome } from "lucide-react";
import { useToast } from "@/hooks/use-toast";


const Landing = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // Check authentication on mount
  useEffect(() => {
    fetch("http://localhost:5000/auth/user", { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        if (data && data.email) {
          navigate("/application");
        }
      });
    // Check for success param in URL
    if (window.location.search.includes("success=true")) {
      toast({ title: "Login Successful!", description: "You are now authenticated.", variant: "default" });
      // Remove param from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [navigate, toast]);

  // Redirect to Flask backend for Google OAuth
  const handleGoogleLogin = () => {
    window.location.href = "http://localhost:5000/auth/google";
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      {/* Subtle background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/3 right-1/3 w-72 h-72 bg-primary/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/3 left-1/3 w-96 h-96 bg-emerald/5 rounded-full blur-3xl"></div>
      </div>

      {/* Main content */}
      <div className="relative z-10 w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-2xl mb-6 shadow-lg">
            <Chrome className="w-8 h-8 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-3">RePrice</h1>
          <p className="text-muted-foreground text-lg">Your intelligent pricing companion</p>
        </div>

        {/* Login Form */}
        <div className="bg-card border border-border rounded-2xl p-8 shadow-lg">
          <h2 className="text-2xl font-semibold text-foreground text-center mb-8">
            Welcome back
          </h2>

          <div className="space-y-4">
            {/* Primary CTA Button */}
            <Button 
              onClick={handleGoogleLogin}
              size="lg" 
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-medium h-12 rounded-xl transition-all duration-200 hover:scale-[1.02]"
            >
              <Chrome className="w-5 h-5 mr-2" />
              Continue with Google
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Landing;