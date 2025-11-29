import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Thermometer, Droplets, Wind, RefreshCw, AlertTriangle, ChevronsUpDown, Check, Search } from "lucide-react";
import { useLiveData } from "@/hooks/useApi";
import { cn } from "@/lib/utils";

const CITIES = [
  // Metro Cities
  { value: "Delhi", label: "Delhi" },
  { value: "Mumbai", label: "Mumbai" },
  { value: "Bangalore", label: "Bangalore" },
  { value: "Chennai", label: "Chennai" },
  { value: "Kolkata", label: "Kolkata" },
  { value: "Hyderabad", label: "Hyderabad" },
  // Major Cities
  { value: "Pune", label: "Pune" },
  { value: "Ahmedabad", label: "Ahmedabad" },
  { value: "Jaipur", label: "Jaipur" },
  { value: "Lucknow", label: "Lucknow" },
  { value: "Kanpur", label: "Kanpur" },
  { value: "Nagpur", label: "Nagpur" },
  { value: "Indore", label: "Indore" },
  { value: "Bhopal", label: "Bhopal" },
  { value: "Patna", label: "Patna" },
  { value: "Vadodara", label: "Vadodara" },
  { value: "Surat", label: "Surat" },
  { value: "Coimbatore", label: "Coimbatore" },
  { value: "Kochi", label: "Kochi" },
  { value: "Visakhapatnam", label: "Visakhapatnam" },
  // State Capitals & Important Cities
  { value: "Chandigarh", label: "Chandigarh" },
  { value: "Thiruvananthapuram", label: "Thiruvananthapuram" },
  { value: "Guwahati", label: "Guwahati" },
  { value: "Bhubaneswar", label: "Bhubaneswar" },
  { value: "Ranchi", label: "Ranchi" },
  { value: "Raipur", label: "Raipur" },
  { value: "Dehradun", label: "Dehradun" },
  { value: "Shimla", label: "Shimla" },
  { value: "Amritsar", label: "Amritsar" },
  { value: "Varanasi", label: "Varanasi" },
  { value: "Agra", label: "Agra" },
  { value: "Mysore", label: "Mysore" },
  { value: "Mangalore", label: "Mangalore" },
  { value: "Madurai", label: "Madurai" },
  { value: "Jodhpur", label: "Jodhpur" },
  { value: "Udaipur", label: "Udaipur" },
  { value: "Goa", label: "Goa" },
  { value: "Pondicherry", label: "Pondicherry" },
];

export default function LiveData() {
  const [selectedCity, setSelectedCity] = useState("Delhi");
  const [fetchEnabled, setFetchEnabled] = useState(false);
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  
  const { data: liveData, isLoading, error, refetch } = useLiveData(selectedCity, fetchEnabled);

  // Filter cities based on search query
  const filteredCities = useMemo(() => {
    if (!searchQuery) return CITIES;
    return CITIES.filter(city => 
      city.label.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [searchQuery]);

  const getAQILevel = (aqi: number) => {
    if (aqi <= 50) return { label: "Good", color: "bg-green-500", textColor: "text-green-500" };
    if (aqi <= 100) return { label: "Moderate", color: "bg-yellow-500", textColor: "text-yellow-500" };
    if (aqi <= 150) return { label: "Unhealthy for Sensitive", color: "bg-orange-500", textColor: "text-orange-500" };
    if (aqi <= 200) return { label: "Unhealthy", color: "bg-red-500", textColor: "text-red-500" };
    return { label: "Very Unhealthy", color: "bg-purple-500", textColor: "text-purple-500" };
  };

  const handleFetchData = () => {
    setFetchEnabled(true);
    refetch();
  };

  return (
    <div className="space-y-6 p-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Live Environmental Data</h1>
          <p className="text-muted-foreground mt-1">
            Real-time weather and air quality from external APIs
          </p>
        </div>
      </div>

      {/* City Selection & Fetch */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="h-5 w-5" />
            Fetch Live Data
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-center flex-wrap">
            <div className="min-w-[280px]">
              <label className="text-sm font-medium mb-2 block">Search & Select City</label>
              <Popover open={open} onOpenChange={setOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={open}
                    className="w-full justify-between h-10"
                  >
                    {selectedCity || "Select a city..."}
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[300px] p-0">
                  <Command>
                    <CommandInput 
                      placeholder="Type to search cities..." 
                      value={searchQuery}
                      onValueChange={setSearchQuery}
                    />
                    <CommandList>
                      <CommandEmpty>No city found.</CommandEmpty>
                      <CommandGroup heading="Indian Cities">
                        {filteredCities.map((city) => (
                          <CommandItem
                            key={city.value}
                            value={city.value}
                            onSelect={(currentValue) => {
                              setSelectedCity(currentValue);
                              setOpen(false);
                              setSearchQuery("");
                            }}
                          >
                            <Check
                              className={cn(
                                "mr-2 h-4 w-4",
                                selectedCity === city.value ? "opacity-100" : "opacity-0"
                              )}
                            />
                            {city.label}
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
              <p className="text-xs text-muted-foreground mt-1">
                {CITIES.length} cities available
              </p>
            </div>
            <Button onClick={handleFetchData} disabled={isLoading} className="gap-2">
              {isLoading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Fetching...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  Fetch Live Data
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-red-500/30 bg-red-500/5">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-6 w-6 text-red-500" />
              <div>
                <p className="font-medium text-red-500">Failed to fetch live data</p>
                <p className="text-sm text-muted-foreground">
                  Make sure the API key is configured and the backend is running.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Live Data Display */}
      {liveData && (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Weather Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Thermometer className="h-5 w-5 text-primary" />
                Weather Data - {selectedCity}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-lg bg-muted/50 text-center">
                  <Thermometer className="h-8 w-8 mx-auto mb-2 text-orange-500" />
                  <p className="text-3xl font-bold font-mono">{liveData.weather.temperature}°C</p>
                  <p className="text-sm text-muted-foreground">Temperature</p>
                </div>
                <div className="p-4 rounded-lg bg-muted/50 text-center">
                  <Droplets className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                  <p className="text-3xl font-bold font-mono">{liveData.weather.humidity}%</p>
                  <p className="text-sm text-muted-foreground">Humidity</p>
                </div>
              </div>
              <div className="p-4 rounded-lg bg-muted/50">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Pressure</span>
                  <span className="font-mono font-medium">{liveData.weather.pressure} hPa</span>
                </div>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Source:</span>
                <Badge variant="outline">{liveData.weather.source}</Badge>
              </div>
            </CardContent>
          </Card>

          {/* Air Quality Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wind className="h-5 w-5 text-primary" />
                Air Quality - {selectedCity}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {(() => {
                const aqiLevel = getAQILevel(liveData.air_quality.aqi);
                return (
                  <>
                    <div className="p-6 rounded-lg bg-muted/50 text-center">
                      <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${aqiLevel.color} text-white mb-3`}>
                        <Wind className="h-5 w-5" />
                        <span className="font-medium">{aqiLevel.label}</span>
                      </div>
                      <p className="text-5xl font-bold font-mono">{liveData.air_quality.aqi}</p>
                      <p className="text-sm text-muted-foreground mt-1">Air Quality Index</p>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 rounded-lg bg-muted/50">
                        <p className="text-sm text-muted-foreground">PM2.5</p>
                        <p className="text-xl font-bold font-mono">{liveData.air_quality.pm25} <span className="text-xs font-normal">µg/m³</span></p>
                      </div>
                      <div className="p-3 rounded-lg bg-muted/50">
                        <p className="text-sm text-muted-foreground">PM10</p>
                        <p className="text-xl font-bold font-mono">{liveData.air_quality.pm10} <span className="text-xs font-normal">µg/m³</span></p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Source:</span>
                      <Badge variant="outline">{liveData.air_quality.source}</Badge>
                    </div>
                  </>
                );
              })()}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Health Impact Advisory */}
      {liveData && liveData.air_quality.aqi > 100 && (
        <Card className="border-orange-500/30 bg-orange-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-500">
              <AlertTriangle className="h-5 w-5" />
              Health Impact Advisory
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">
              Current AQI of <strong>{liveData.air_quality.aqi}</strong> may increase respiratory admissions by 
              <strong> 15-20%</strong> in the next 48 hours. Consider:
            </p>
            <ul className="mt-3 space-y-1 text-sm text-muted-foreground">
              <li>• Preparing additional respiratory care resources</li>
              <li>• Alerting pulmonology and emergency departments</li>
              <li>• Increasing ventilator availability</li>
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Timestamp */}
      {liveData && (
        <p className="text-sm text-muted-foreground text-center">
          Last updated: {new Date(liveData.timestamp).toLocaleString()}
        </p>
      )}
    </div>
  );
}
