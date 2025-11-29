import { useState, useCallback, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Upload, FileSpreadsheet, CheckCircle, XCircle, AlertTriangle, Download, Trash2, RefreshCw } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface UploadedFile {
  name: string;
  size: number;
  status: "pending" | "processing" | "success" | "error";
  rows?: number;
  columns?: string[];
  error?: string;
  hospitalId?: string;
  dateRange?: { start: string; end: string };
  validation?: {
    columns_found: string[];
    columns_generated: string[];
    warnings: string[];
  };
}

interface UploadStatus {
  has_uploads: boolean;
  uploads: Array<{
    hospital_id: string;
    rows: number;
    columns: string[];
    date_range: { start: string; end: string };
  }>;
}

export default function DataUpload() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  // Fetch current upload status on mount
  useEffect(() => {
    fetchUploadStatus();
  }, []);

  const fetchUploadStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/upload/status`);
      if (response.ok) {
        const data = await response.json();
        setUploadStatus(data);
      }
    } catch (error) {
      console.error("Failed to fetch upload status:", error);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const processFile = async (file: File) => {
    const newFile: UploadedFile = {
      name: file.name,
      size: file.size,
      status: "processing",
    };
    
    setFiles(prev => [...prev, newFile]);
    setUploadProgress(10);

    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', file);

      setUploadProgress(30);

      // Upload to backend
      const response = await fetch(`${API_BASE}/api/upload?hospital_id=UPLOADED`, {
        method: 'POST',
        body: formData,
      });

      setUploadProgress(70);

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Upload failed');
      }

      setUploadProgress(100);

      // Update file status with server response
      setFiles(prev => prev.map(f => 
        f.name === file.name 
          ? {
              ...f,
              status: "success",
              rows: result.rows,
              columns: result.columns,
              hospitalId: result.hospital_id,
              dateRange: result.date_range,
              validation: result.validation
            }
          : f
      ));

      toast({
        title: "Upload Successful",
        description: `${result.rows} rows of data uploaded. Dashboard will now use your real data!`,
      });

      // Refresh upload status
      fetchUploadStatus();

    } catch (error) {
      console.error('Upload error:', error);
      
      setFiles(prev => prev.map(f => 
        f.name === file.name 
          ? {
              ...f,
              status: "error",
              error: error instanceof Error ? error.message : 'Upload failed'
            }
          : f
      ));

      toast({
        title: "Upload Failed",
        description: error instanceof Error ? error.message : 'Failed to upload file',
        variant: "destructive",
      });
    } finally {
      setTimeout(() => setUploadProgress(0), 500);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    droppedFiles.forEach(file => {
      if (file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        processFile(file);
      } else {
        toast({
          title: "Invalid File Type",
          description: "Please upload CSV or Excel files only",
          variant: "destructive",
        });
      }
    });
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    selectedFiles.forEach(file => {
      if (file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        processFile(file);
      }
    });
  };

  const removeFile = (fileName: string) => {
    setFiles(prev => prev.filter(f => f.name !== fileName));
  };

  const deleteUploadedData = async (hospitalId: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/upload/${hospitalId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        toast({
          title: "Data Deleted",
          description: "Uploaded data has been removed. Dashboard will use simulated data.",
        });
        fetchUploadStatus();
        setFiles(prev => prev.filter(f => f.hospitalId !== hospitalId));
      }
    } catch (error) {
      toast({
        title: "Delete Failed",
        description: "Failed to delete uploaded data",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const downloadTemplate = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/upload/template`);
      const data = await response.json();
      
      // Convert to CSV
      const headers = Object.keys(data);
      const rows = data.date.map((_: string, i: number) => 
        headers.map(h => data[h][i]).join(',')
      );
      const csvContent = [headers.join(','), ...rows].join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'hospitai_template.csv';
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      // Fallback to static template
      const csvContent = `date,occupied_beds,total_beds,occupied_icu,total_icu_beds,ventilators_used,total_ventilators,staff_on_duty,flu_cases,temperature,humidity,pollution
2025-01-01,150,200,22,30,12,20,130,45,15.5,65,85
2025-01-02,155,200,24,30,14,20,125,48,14.2,68,92
2025-01-03,148,200,21,30,11,20,135,42,16.1,62,78`;
      
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'hospitai_template.csv';
      a.click();
      window.URL.revokeObjectURL(url);
    }
  };


  return (
    <div className="space-y-6 p-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Upload</h1>
          <p className="text-muted-foreground mt-1">
            Upload your hospital data in CSV or Excel format
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchUploadStatus} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline" onClick={downloadTemplate} className="gap-2">
            <Download className="h-4 w-4" />
            Download Template
          </Button>
        </div>
      </div>

      {/* Current Upload Status */}
      {uploadStatus?.has_uploads && (
        <Card className="border-green-500/50 bg-green-500/5">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              Active Uploaded Data
            </CardTitle>
          </CardHeader>
          <CardContent>
            {uploadStatus.uploads.map((upload) => (
              <div key={upload.hospital_id} className="flex items-center justify-between p-3 rounded-lg bg-background">
                <div>
                  <p className="font-medium">Hospital ID: {upload.hospital_id}</p>
                  <p className="text-sm text-muted-foreground">
                    {upload.rows} rows • {upload.date_range.start.split('T')[0]} to {upload.date_range.end.split('T')[0]}
                  </p>
                </div>
                <Button 
                  variant="destructive" 
                  size="sm"
                  onClick={() => deleteUploadedData(upload.hospital_id)}
                  disabled={isLoading}
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Remove
                </Button>
              </div>
            ))}
            <p className="text-sm text-green-600 mt-3">
              ✓ Dashboard is using your uploaded data instead of simulated data
            </p>
          </CardContent>
        </Card>
      )}

      {/* Upload Zone */}
      <Card>
        <CardContent className="pt-6">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`
              border-2 border-dashed rounded-lg p-12 text-center transition-all
              ${isDragging 
                ? 'border-primary bg-primary/5' 
                : 'border-muted-foreground/25 hover:border-primary/50'
              }
            `}
          >
            <Upload className={`h-12 w-12 mx-auto mb-4 ${isDragging ? 'text-primary' : 'text-muted-foreground'}`} />
            <h3 className="text-lg font-semibold mb-2">
              {isDragging ? 'Drop files here' : 'Drag & drop files here'}
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              or click to browse
            </p>
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload">
              <Button variant="outline" className="cursor-pointer" asChild>
                <span>Select Files</span>
              </Button>
            </label>
            <p className="text-xs text-muted-foreground mt-4">
              Supported formats: CSV, Excel (.xlsx, .xls) • Max size: 10MB
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Upload Progress */}
      {uploadProgress > 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Uploading & Processing...</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Uploaded Files */}
      {files.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Upload History ({files.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {files.map((file) => (
              <div
                key={file.name}
                className="flex items-start gap-4 p-4 rounded-lg border bg-card"
              >
                <div className="p-2 rounded-lg bg-muted">
                  <FileSpreadsheet className="h-6 w-6 text-green-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium truncate">{file.name}</p>
                    {file.status === "success" && (
                      <Badge className="bg-green-500">Processed</Badge>
                    )}
                    {file.status === "processing" && (
                      <Badge variant="outline">Processing...</Badge>
                    )}
                    {file.status === "error" && (
                      <Badge variant="destructive">Error</Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                    <span>{formatFileSize(file.size)}</span>
                    {file.rows && <span>{file.rows} rows</span>}
                    {file.columns && <span>{file.columns.length} columns</span>}
                  </div>
                  {file.dateRange && (
                    <p className="text-sm text-muted-foreground mt-1">
                      Date range: {file.dateRange.start.split('T')[0]} to {file.dateRange.end.split('T')[0]}
                    </p>
                  )}
                  {file.validation?.warnings && file.validation.warnings.length > 0 && (
                    <div className="mt-2">
                      {file.validation.warnings.map((warning, i) => (
                        <p key={i} className="text-sm text-yellow-600 flex items-center gap-1">
                          <AlertTriangle className="h-3 w-3" />
                          {warning}
                        </p>
                      ))}
                    </div>
                  )}
                  {file.error && (
                    <p className="text-sm text-red-500 mt-1 flex items-center gap-1">
                      <XCircle className="h-3 w-3" />
                      {file.error}
                    </p>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeFile(file.name)}
                  className="text-muted-foreground hover:text-red-500"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Data Requirements */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
            Data Requirements
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <h4 className="font-medium mb-3">Required Columns</h4>
              <ul className="space-y-2 text-sm">
                {[
                  { name: "date", desc: "Date in YYYY-MM-DD format" },
                  { name: "occupied_beds", desc: "Number of occupied beds" },
                  { name: "total_beds", desc: "Total bed capacity" },
                ].map((col) => (
                  <li key={col.name} className="flex items-start gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                    <div>
                      <code className="bg-muted px-1 rounded text-xs">{col.name}</code>
                      <span className="text-muted-foreground ml-2">{col.desc}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-3">Optional Columns (auto-generated if missing)</h4>
              <ul className="space-y-2 text-sm">
                {[
                  { name: "occupied_icu", desc: "ICU beds in use" },
                  { name: "total_icu_beds", desc: "Total ICU capacity" },
                  { name: "ventilators_used", desc: "Ventilators in use" },
                  { name: "staff_on_duty", desc: "Staff count" },
                  { name: "flu_cases", desc: "Regional flu cases" },
                  { name: "temperature", desc: "Temperature (°C)" },
                  { name: "pollution", desc: "AQI value" },
                ].map((col) => (
                  <li key={col.name} className="flex items-start gap-2">
                    <div className="h-4 w-4 rounded-full border-2 border-muted-foreground/30 mt-0.5" />
                    <div>
                      <code className="bg-muted px-1 rounded text-xs">{col.name}</code>
                      <span className="text-muted-foreground ml-2">{col.desc}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sample Data Preview */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Sample Data Format</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3 font-medium">date</th>
                  <th className="text-left py-2 px-3 font-medium">occupied_beds</th>
                  <th className="text-left py-2 px-3 font-medium">total_beds</th>
                  <th className="text-left py-2 px-3 font-medium">occupied_icu</th>
                  <th className="text-left py-2 px-3 font-medium">flu_cases</th>
                  <th className="text-left py-2 px-3 font-medium">pollution</th>
                </tr>
              </thead>
              <tbody className="font-mono text-xs">
                <tr className="border-b border-muted">
                  <td className="py-2 px-3">2025-01-01</td>
                  <td className="py-2 px-3">150</td>
                  <td className="py-2 px-3">200</td>
                  <td className="py-2 px-3">22</td>
                  <td className="py-2 px-3">45</td>
                  <td className="py-2 px-3">85</td>
                </tr>
                <tr className="border-b border-muted">
                  <td className="py-2 px-3">2025-01-02</td>
                  <td className="py-2 px-3">155</td>
                  <td className="py-2 px-3">200</td>
                  <td className="py-2 px-3">24</td>
                  <td className="py-2 px-3">48</td>
                  <td className="py-2 px-3">92</td>
                </tr>
                <tr>
                  <td className="py-2 px-3">2025-01-03</td>
                  <td className="py-2 px-3">148</td>
                  <td className="py-2 px-3">200</td>
                  <td className="py-2 px-3">21</td>
                  <td className="py-2 px-3">42</td>
                  <td className="py-2 px-3">78</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
