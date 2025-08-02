import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sidebar, SidebarContent, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Package, DollarSign, Settings, User, Clock, Shield, AlertTriangle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { updateProductStatus, fetchProducts } from "@/lib/productApi";

interface Product {
  id: number;
  itemname: string;
  purchase_price: number;
  purchase_date: string;
  price_range: string;
  confidence: string;
  status: string;
}

const ReSale = () => {
  const navigate = useNavigate();
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    fetch("http://localhost:5000/auth/user", { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        if (data && data.email) setUserEmail(data.email);
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
        if (!data || !data.email) {
          navigate("/");
        }
      });
  }, [navigate]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProducts()
      .then(data => {
        setProducts(data.products);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Status click logic
  const handleStatusClick = async (product: Product) => {
    let newStatus = '';
    if (product.status === 'uncertain') newStatus = 'dont_sell';
    else if (product.status === 'dont_sell') newStatus = 'resell_candidate';
    else if (product.status === 'resell_candidate') newStatus = 'dont_sell';
    else return;
    try {
      await updateProductStatus(product.id, newStatus);
      // Refetch products after update
      fetchProducts()
        .then(data => {
          setProducts(data.products);
        });
    } catch (e) {
      alert('Failed to update status');
    }
  };

  const truncateItemName = (itemname: string) => {
    const words = itemname.split(' ');
    return words.slice(0, 5).join(' ');
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'resell_candidate':
        return 'destructive';
      case 'uncertain':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const getConfidenceIcon = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return <Shield className="w-4 h-4 text-green-500" />;
      case 'medium':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'low':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen bg-background flex">
        {/* Sidebar */}
        <Sidebar className="border-r border-sidebar-border bg-sidebar">
          <SidebarContent className="p-4">
            <div className="space-y-6">
              {/* User profile */}
              <div className="text-center">
                <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center mx-auto mb-3 transition-transform hover:scale-105">
                  <User className="w-6 h-6 text-primary-foreground" />
                </div>
                <p className="text-sidebar-foreground text-sm font-medium truncate">{userEmail}</p>
              </div>

              {/* Navigation */}
              <nav className="space-y-2">
                <div 
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-sidebar-accent transition-colors cursor-pointer group"
                  onClick={() => navigate('/application')}
                >
                  <Package className="w-5 h-5 text-blue group-hover:text-primary transition-colors" />
                  <span className="text-sidebar-foreground group-hover:text-sidebar-accent-foreground">Unused Items</span>
                </div>
                
                <div className="flex items-center space-x-3 p-3 rounded-lg bg-primary text-primary-foreground">
                  <DollarSign className="w-5 h-5" />
                  <span className="font-medium">ReSale Value</span>
                </div>
                
                <div 
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-sidebar-accent transition-colors cursor-pointer group"
                  onClick={() => navigate('/settings')}
                >
                  <Settings className="w-5 h-5 text-purple group-hover:text-primary transition-colors" />
                  <span className="text-sidebar-foreground group-hover:text-sidebar-accent-foreground">Settings</span>
                </div>
              </nav>
            </div>
          </SidebarContent>
        </Sidebar>

        {/* Main content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm p-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <SidebarTrigger />
              <div>
                <h1 className="text-xl font-semibold text-foreground">ReSale Value</h1>
                <p className="text-sm text-muted-foreground">{products.length} total items tracked</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button 
                variant="outline"
                size="sm"
                onClick={async () => {
                  await fetch("http://localhost:5000/auth/logout", {
                    method: "POST",
                    credentials: "include"
                  });
                  navigate("/");
                }}
              >
                Logout
              </Button>
            </div>
          </header>

          {/* Items grid */}
          <main className="flex-1 p-6">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {products.map((product) => (
                <Card 
                  key={product.id} 
                  className="group hover:shadow-md transition-all duration-200 border-border/50"
                >
                  {/* Card Header */}
                  <div className="p-4 pb-3">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-semibold text-foreground text-lg leading-tight">
                        {truncateItemName(product.itemname)}
                      </h3>
                      <Badge
            variant={getStatusVariant(product.status)}
            className="ml-2 shrink-0 cursor-pointer hover:scale-105 transition-transform"
            onClick={() => handleStatusClick(product)}
            title="Click to change status"
          >
            {/* Show 'resell' instead of 'resell_candidate' */}
            {product.status === 'resell_candidate' ? 'resell' : product.status.replace('_', ' ')}
          </Badge>

                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                      <Clock className="w-4 h-4 text-cyan" />
                      <span>Purchased {new Date(product.purchase_date).toLocaleDateString()}</span>
                    </div>
                  </div>
                  
                  {/* Price Section */}
                  <div className="px-4 pb-4">
                    <div className="bg-muted/30 rounded-lg p-3 mb-3 space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-muted-foreground uppercase tracking-wide">Purchase Price</span>
                        <span className="text-lg font-bold text-foreground">₹{product.purchase_price.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-muted-foreground uppercase tracking-wide">Current Range</span>
                        <span className="text-sm font-semibold text-orange">{product.price_range}</span>
                      </div>
                    </div>
                    
                    
                  </div>
                </Card>
                ))}
              </div>
            )}
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default ReSale;