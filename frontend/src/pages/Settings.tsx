import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Sidebar, SidebarContent, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Package, DollarSign, Settings as SettingsIcon, User, Shield, Eye, Database, Smartphone, Mail, Bell, Globe, Lock, FileText } from "lucide-react";
import { useNavigate } from "react-router-dom";

const Settings = () => {
  const navigate = useNavigate();

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
        if (!data || !data.email) {
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

  // Fetch consent status on mount
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

  // Handle toggle for consent protocol
  const handlePermissionChange = async (permission: string, value: boolean) => {
    setPermissions(prev => ({
      ...prev,
      [permission]: value
    }));

    // Handle consent for emailTracking, calendarAccess, browserHistory, deviceInfo
    if (permission === 'emailTracking') {
      if (value) {
        await fetch("http://localhost:5000/consent/generate-token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ type: "gmail" })
        });
      } else {
        await fetch("http://localhost:5000/consent/revoke-token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ type: "gmail" })
        });
      }
    }
    if (permission === 'calendarAccess') {
      if (value) {
        await fetch("http://localhost:5000/consent/generate-token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ type: "calendar" })
        });
      } else {
        await fetch("http://localhost:5000/consent/revoke-token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ type: "calendar" })
        });
      }
    }
    if (permission === 'browserHistory') {
      if (value) {
        await fetch("http://localhost:5000/consent/generate-token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ type: "browser_history" })
        });
      } else {
        await fetch("http://localhost:5000/consent/revoke-token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ type: "browser_history" })
        });
      }
    }
    if (permission === 'deviceInfo') {
      if (value) {
        await fetch("http://localhost:5000/consent/generate-token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ type: "driver" })
        });
      } else {
        await fetch("http://localhost:5000/consent/revoke-token", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ type: "driver" })
        });
      }
    }
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen bg-background flex">
        {/* Sidebar */}
        <Sidebar className="border-r border-sidebar-border bg-sidebar">
          <SidebarContent className="p-6">
            <div className="space-y-8">
              {/* User profile */}
              <div className="text-center">
                <div className="w-12 h-12 bg-sidebar-primary rounded-full flex items-center justify-center mx-auto mb-4">
                  <User className="w-6 h-6 text-sidebar-primary-foreground" />
                </div>
                <p className="text-sidebar-foreground text-sm">johndoe@gmail.com</p>
              </div>

              {/* Navigation */}
              <nav className="space-y-2">
                <div 
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors cursor-pointer"
                  onClick={() => navigate('/application')}
                >
                  <Package className="w-5 h-5" />
                  <span>Unused Items</span>
                </div>
                
                <div 
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors cursor-pointer"
                  onClick={() => navigate('/resale')}
                >
                  <DollarSign className="w-5 h-5" />
                  <span>ReSale Value</span>
                </div>
                
                <div className="flex items-center space-x-3 p-3 rounded-lg bg-sidebar-accent text-sidebar-accent-foreground">
                  <SettingsIcon className="w-5 h-5" />
                  <span className="font-medium">Settings</span>
                </div>
              </nav>
            </div>
          </SidebarContent>
        </Sidebar>

        {/* Main content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="sticky top-0 z-50 border-b border-border bg-card/95 backdrop-blur-sm p-4 sm:p-6 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <SidebarTrigger />
              <h1 className="text-lg sm:text-2xl font-bold text-foreground">RePrice • Settings</h1>
            </div>
            
            <div className="flex items-center space-x-2 sm:space-x-4">
              <div className="hidden sm:block text-sm text-muted-foreground">
                Welcome back!
              </div>
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-primary-foreground" />
              </div>
            </div>
          </header>

          {/* Settings content */}
          <main className="flex-1 p-4 sm:p-8 bg-gradient-subtle w-full">
            <div className="w-full space-y-8">
              <div className="text-center">
                <h2 className="text-4xl font-bold text-foreground mb-3 bg-gradient-primary bg-clip-text text-transparent">
                  Settings & Preferences
                </h2>
                <p className="text-muted-foreground text-lg">Customize your RePrice experience</p>
              </div>

              {/* Privacy & Permissions Card */}
              <Card className="bg-gradient-card border border-border/50 shadow-elegant hover:shadow-glow transition-all duration-300">
                <CardHeader className="bg-muted/30 rounded-t-xl">
                  <CardTitle className="flex items-center gap-3 text-xl">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <Shield className="w-6 h-6 text-primary" />
                    </div>
                    Privacy & Data Permissions
                  </CardTitle>
                  <CardDescription className="text-base">
                    Control what data we can access to provide personalized recommendations and accurate pricing
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-8 space-y-8">
                  <div className="grid gap-6">
                    <div className="flex items-center justify-between p-4 rounded-xl bg-muted/20 hover:bg-muted/30 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                          <Globe className="w-5 h-5 text-blue-500" />
                        </div>
                        <div className="space-y-1">
                          <Label htmlFor="browser-history" className="text-base font-semibold">
                            Browser History Access
                          </Label>
                          <p className="text-sm text-muted-foreground">
                            Track product research and shopping patterns for better recommendations
                          </p>
                        </div>
                      </div>
                      <Switch
                        id="browser-history"
                        checked={permissions.browserHistory}
                        onCheckedChange={(checked) => handlePermissionChange('browserHistory', checked)}
                        className="data-[state=checked]:bg-primary"
                      />
                    </div>

                    <Separator className="bg-border/50" />

                    <div className="flex items-center justify-between p-4 rounded-xl bg-muted/20 hover:bg-muted/30 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="p-2 bg-green-500/10 rounded-lg">
                          <FileText className="w-5 h-5 text-green-500" />
                        </div>
                        <div className="space-y-1">
                          <Label htmlFor="calendar-access" className="text-base font-semibold">
                            Calendar Integration
                          </Label>
                          <p className="text-sm text-muted-foreground">
                            Automatically detect purchase dates from calendar events and receipts
                          </p>
                        </div>
                      </div>
                      <Switch
                        id="calendar-access"
                        checked={permissions.calendarAccess}
                        onCheckedChange={(checked) => handlePermissionChange('calendarAccess', checked)}
                        className="data-[state=checked]:bg-primary"
                      />
                    </div>

                    <Separator className="bg-border/50" />

                    <div className="flex items-center justify-between p-4 rounded-xl bg-muted/20 hover:bg-muted/30 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="p-2 bg-purple-500/10 rounded-lg">
                          <Mail className="w-5 h-5 text-purple-500" />
                        </div>
                        <div className="space-y-1">
                          <Label htmlFor="email-tracking" className="text-base font-semibold">
                            Email Receipt Scanning
                          </Label>
                          <p className="text-sm text-muted-foreground">
                            Scan email receipts to automatically add purchases and track warranties
                          </p>
                        </div>
                      </div>
                      <Switch
                        id="email-tracking"
                        checked={permissions.emailTracking}
                        onCheckedChange={(checked) => handlePermissionChange('emailTracking', checked)}
                        className="data-[state=checked]:bg-primary"
                      />
                    </div>

                    <Separator className="bg-border/50" />

                    <div className="flex items-center justify-between p-4 rounded-xl bg-muted/20 hover:bg-muted/30 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="p-2 bg-yellow-500/10 rounded-lg">
                          <Bell className="w-5 h-5 text-yellow-500" />
                        </div>
                        <div className="space-y-1">
                          <Label htmlFor="notifications" className="text-base font-semibold">
                            Smart Notifications
                          </Label>
                          <p className="text-sm text-muted-foreground">
                            Receive alerts for price drops, resale opportunities, and market trends
                          </p>
                        </div>
                      </div>
                      <Switch
                        id="notifications"
                        checked={permissions.notifications}
                        onCheckedChange={(checked) => handlePermissionChange('notifications', checked)}
                        className="data-[state=checked]:bg-primary"
                      />
                    </div>

                    <Separator className="bg-border/50" />

                    <div className="flex items-center justify-between p-4 rounded-xl bg-muted/20 hover:bg-muted/30 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="p-2 bg-orange-500/10 rounded-lg">
                          <Smartphone className="w-5 h-5 text-orange-500" />
                        </div>
                        <div className="space-y-1">
                          <Label htmlFor="device-info" className="text-base font-semibold">
                            Device Information
                          </Label>
                          <p className="text-sm text-muted-foreground">
                            Access device specs to provide accurate compatibility and pricing data
                          </p>
                        </div>
                      </div>
                      <Switch
                        id="device-info"
                        checked={permissions.deviceInfo}
                        onCheckedChange={(checked) => handlePermissionChange('deviceInfo', checked)}
                        className="data-[state=checked]:bg-primary"
                      />
                    </div>

                    <Separator className="bg-border/50" />

                    <div className="flex items-center justify-between p-4 rounded-xl bg-muted/20 hover:bg-muted/30 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="p-2 bg-red-500/10 rounded-lg">
                          <Lock className="w-5 h-5 text-red-500" />
                        </div>
                        <div className="space-y-1">
                          <Label htmlFor="third-party-sharing" className="text-base font-semibold">
                            Third-Party Data Sharing
                          </Label>
                          <p className="text-sm text-muted-foreground">
                            Share anonymized data with partners to improve pricing accuracy
                          </p>
                        </div>
                      </div>
                      <Switch
                        id="third-party-sharing"
                        checked={permissions.thirdPartySharing}
                        onCheckedChange={(checked) => handlePermissionChange('thirdPartySharing', checked)}
                        className="data-[state=checked]:bg-primary"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Data Analytics Card */}
              <Card className="bg-gradient-card border border-border/50 shadow-elegant hover:shadow-glow transition-all duration-300">
                <CardHeader className="bg-muted/30 rounded-t-xl">
                  <CardTitle className="flex items-center gap-3 text-xl">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <Database className="w-6 h-6 text-primary" />
                    </div>
                    Analytics & Performance
                  </CardTitle>
                  <CardDescription className="text-base">
                    Help us improve RePrice by sharing anonymous usage data
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-8">
                  <div className="flex items-center justify-between p-4 rounded-xl bg-muted/20 hover:bg-muted/30 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className="p-2 bg-cyan-500/10 rounded-lg">
                        <Eye className="w-5 h-5 text-cyan-500" />
                      </div>
                      <div className="space-y-1">
                        <Label htmlFor="analytics" className="text-base font-semibold">
                          Usage Analytics
                        </Label>
                        <p className="text-sm text-muted-foreground">
                          Share anonymous app usage data to help us improve features and performance
                        </p>
                      </div>
                    </div>
                    <Switch
                      id="analytics"
                      checked={permissions.analytics}
                      onCheckedChange={(checked) => handlePermissionChange('analytics', checked)}
                      className="data-[state=checked]:bg-primary"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Action Buttons */}
              <div className="flex justify-between items-center pt-6">
                <Button 
                  variant="outline" 
                  className="px-8 py-3 text-base border-border/50 hover:bg-muted/50"
                  onClick={() => setPermissions({
                    browserHistory: true,
                    calendarAccess: true,
                    dataCollection: true,
                    notifications: true,
                    analytics: true,
                    locationAccess: true,
                    emailTracking: true,
                    deviceInfo: true,
                    thirdPartySharing: true,
                  })}
                >
                  Reset to Defaults
                </Button>
                <Button className="bg-gradient-primary hover:opacity-90 text-white font-semibold px-12 py-3 text-base rounded-xl shadow-glow">
                  Save All Settings
                </Button>
              </div>
            </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Settings;