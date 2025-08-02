import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Sidebar, SidebarContent, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import {
  Package, DollarSign, Settings as SettingsIcon, User, Shield,
  Globe, Mail, FileText, Smartphone
} from "lucide-react";
import { useNavigate } from "react-router-dom";

const Settings = () => {
  const navigate = useNavigate();
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    fetch("http://localhost:5000/auth/user", { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        if (data?.email) setUserEmail(data.email);
      });
  }, []);

  useEffect(() => {
    fetch("http://localhost:5000/auth/user", { credentials: "include" })
      .then(res => {
        if (!res.ok) {
          navigate("/");
          return;
        }
        return res.json();
      })
      .then(data => {
        if (!data?.email) {
          navigate("/");
        }
      });
  }, [navigate]);

  const [permissions, setPermissions] = useState({
    browserHistory: true,
    calendarAccess: false,
    dataCollection: true,
    notifications: true,
    analytics: false,
    locationAccess: false,
    emailTracking: false,
    deviceInfo: false,
    thirdPartySharing: false,
  });

  useEffect(() => {
    fetch("http://localhost:5000/consent/status", { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        setPermissions(prev => ({
          ...prev,
          emailTracking: !!data.gmail,
          calendarAccess: !!data.calendar,
          browserHistory: !!data.browser_history,
          deviceInfo: !!data.driver
        }));
      });
  }, []);

  const handlePermissionChange = async (permission: string, value: boolean) => {
    setPermissions(prev => ({
      ...prev,
      [permission]: value
    }));

    const typeMap: Record<string, string> = {
      emailTracking: "gmail",
      calendarAccess: "calendar",
      browserHistory: "browser_history",
      deviceInfo: "driver",
    };

    if (typeMap[permission]) {
      const endpoint = value ? "generate-token" : "revoke-token";
      await fetch(`http://localhost:5000/consent/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ type: typeMap[permission] }),
      });
    }
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen bg-background flex w-full">
        {/* Sidebar */}
        <Sidebar className="border-r border-sidebar-border bg-sidebar">
          <SidebarContent className="p-4">
            <div className="space-y-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center mx-auto mb-3 transition-transform hover:scale-105">
                  <User className="w-6 h-6 text-primary-foreground" />
                </div>
                <p className="text-sidebar-foreground text-sm font-medium truncate">{userEmail}</p>
              </div>

              <nav className="space-y-2">
                <div
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-sidebar-accent transition-colors cursor-pointer group"
                  onClick={() => navigate('/application')}
                >
                  <DollarSign className="w-5 h-5" />
                  
                  <span className="text-sidebar-foreground group-hover:text-sidebar-accent-foreground">Resalable items</span>
                </div>

                <div
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-sidebar-accent transition-colors cursor-pointer group"
                  onClick={() => navigate('/resale')}
                >
                  <Package className="w-5 h-5" />
                  <span className="text-sidebar-foreground group-hover:text-sidebar-accent-foreground">All Products</span>
                </div>

                <div className="flex items-center space-x-3 p-3 rounded-lg bg-primary text-primary-foreground">
                  <SettingsIcon className="w-5 h-5" />
                  <span className="font-medium">Settings</span>
                </div>
              </nav>
            </div>
          </SidebarContent>
        </Sidebar>

        {/* Main Content */}
        <div className="flex flex-col flex-1 w-full">
          {/* Header */}
          <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm p-4 w-full flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <SidebarTrigger />
              <div>
                <h1 className="text-xl font-semibold text-foreground">Settings</h1>
                <p className="text-sm text-muted-foreground">Manage your account preferences</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  await fetch("http://localhost:5000/auth/logout", {
                    method: "POST",
                    credentials: "include",
                  });
                  navigate("/");
                }}
              >
                Logout
              </Button>
            </div>
          </header>

          {/* Settings content */}
          <main className="flex-1 w-full p-6">
            <div className="mx-auto max-w-4xl space-y-8">
              <Card className="border-border shadow-sm">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center gap-3 text-xl">
                    <div className="p-2 bg-purple/10 rounded-lg">
                      <Shield className="w-5 h-5 text-purple" />
                    </div>
                    Privacy & Data Permissions
                  </CardTitle>
                  <CardDescription>
                    Control what data we can access to provide personalized recommendations
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {[
                    {
                      icon: <Globe className="w-5 h-5 text-blue" />,
                      id: "browser-history",
                      label: "Browser History Access",
                      description: "Track product research and shopping patterns",
                      stateKey: "browserHistory",
                    },
                    {
                      icon: <FileText className="w-5 h-5 text-emerald" />,
                      id: "calendar-access",
                      label: "Calendar Integration",
                      description: "Detect purchase dates from calendar events",
                      stateKey: "calendarAccess",
                    },
                    {
                      icon: <Mail className="w-5 h-5 text-purple" />,
                      id: "email-tracking",
                      label: "Email Receipt Scanning",
                      description: "Scan email receipts to track purchases",
                      stateKey: "emailTracking",
                    },
                    {
                      icon: <Smartphone className="w-5 h-5 text-orange" />,
                      id: "device-info",
                      label: "Device Information",
                      description: "Access device specs for accurate pricing",
                      stateKey: "deviceInfo",
                    },
                  ].map(({ icon, id, label, description, stateKey }) => (
                    <div key={id} className="flex items-center justify-between p-4 rounded-lg border border-border/50 bg-card/50">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-muted/10">
                          {icon}
                        </div>
                        <div>
                          <Label htmlFor={id} className="font-medium text-foreground">{label}</Label>
                          <p className="text-sm text-muted-foreground">{description}</p>
                        </div>
                      </div>
                      <Switch
                        id={id}
                        checked={permissions[stateKey as keyof typeof permissions]}
                        onCheckedChange={(checked) => handlePermissionChange(stateKey, checked)}
                      />
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Settings;
