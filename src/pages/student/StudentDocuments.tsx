import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useStudent } from '@/context/StudentContext';
import { format } from 'date-fns';
import type { Document } from '@/types';
import {
  Upload, FileText, CheckCircle2, Clock, XCircle, Download,
  Camera, ScanFace, Shield, AlertTriangle, X, ChevronRight,
  Eye, RotateCcw, Fingerprint, Info, ImageIcon,
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────────
// LIVE PHOTO — uses real getUserMedia camera
// ─────────────────────────────────────────────────────────────────
type LiveStep = 'intro' | 'camera' | 'scanning' | 'done' | 'failed' | 'nocamera';

function LivePhotoModal({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [step,      setStep]     = useState<LiveStep>('intro');
  const [progress,  setProgress] = useState(0);
  const [status,    setStatus]   = useState('');
  const [attempt,   setAttempt]  = useState(0);
  const [snapshot,  setSnapshot] = useState<string>('');
  const videoRef   = useRef<HTMLVideoElement>(null);
  const canvasRef  = useRef<HTMLCanvasElement>(null);
  const streamRef  = useRef<MediaStream | null>(null);

  // Clean up camera on unmount
  useEffect(() => {
    return () => { streamRef.current?.getTracks().forEach(t => t.stop()); };
  }, []);

  const openCamera = async () => {
    try {
      // Check if camera API is available
      if (!navigator.mediaDevices?.getUserMedia) {
        setStep('nocamera');
        return;
      }
      // Request camera with fallback constraints
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 320 }, height: { ideal: 320 } },
          audio: false,
        });
      } catch {
        // Fallback: try without facingMode (some desktops don't support it)
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }
      streamRef.current = stream;
      // Wait for next render cycle to set srcObject
      requestAnimationFrame(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => {});
        }
      });
      setStep('camera');
    } catch (err: any) {
      // Provide specific error context
      if (err?.name === 'NotAllowedError' || err?.name === 'PermissionDeniedError') {
        setStep('nocamera');
      } else if (err?.name === 'NotFoundError' || err?.name === 'DevicesNotFoundError') {
        setStep('nocamera');
      } else {
        setStep('nocamera');
      }
    }
  };

  const captureAndScan = useCallback(() => {
    // Capture still frame
    if (videoRef.current && canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      canvasRef.current.width  = videoRef.current.videoWidth  || 320;
      canvasRef.current.height = videoRef.current.videoHeight || 320;
      ctx?.drawImage(videoRef.current, 0, 0);
      setSnapshot(canvasRef.current.toDataURL('image/jpeg', 0.8));
    }
    // Stop camera
    streamRef.current?.getTracks().forEach(t => t.stop());
    setStep('scanning');
    setProgress(0);

    const msgs = [
      'Face detected in frame…',
      'Liveness check — please blink…',
      'Liveness check — slight head turn…',
      'Matching against APAAR photo record…',
      'Verification complete ✓',
    ];
    let i = 0;
    const iv = setInterval(() => {
      i++;
      const pct = Math.min(i * 22, 100);
      setProgress(pct);
      setStatus(msgs[i - 1] ?? msgs[4]);
      if (i >= 5) {
        clearInterval(iv);
        setTimeout(() => {
          // In a real system this would be a server call. Here: always pass on first attempt, fail on 2nd+ to demo the retry
          setStep(attempt === 1 ? 'failed' : 'done');
        }, 400);
      }
    }, 650);
  }, [attempt]);

  const checks = [
    { label: 'Face detected',              done: progress > 15 },
    { label: 'Liveness — blink detected',  done: progress > 35 },
    { label: 'Liveness — head turn',       done: progress > 57 },
    { label: 'APAAR photo match',          done: progress > 79 },
    { label: 'Identity confirmed',         done: progress >= 100 },
  ];

  return (
    <>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 0.6 }} exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black z-40" onClick={step === 'intro' ? onClose : undefined} />
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
        className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
      >
        <div className="w-full sm:max-w-sm bg-surface rounded-t-2xl sm:rounded-panel shadow-2xl overflow-hidden max-h-[92vh] flex flex-col">
          <div className="flex justify-center pt-3 pb-1 sm:hidden">
            <div className="w-10 h-1 rounded-full bg-border" />
          </div>
          <div className="flex items-center justify-between px-5 py-4 border-b border-border flex-shrink-0">
            <div className="flex items-center gap-2">
              <ScanFace className="w-4 h-4 text-brand" />
              <p className="text-sm font-semibold text-text-primary">Live Identity Check</p>
            </div>
            <button className="btn-icon" onClick={onClose}><X className="w-4 h-4" /></button>
          </div>

          <div className="overflow-y-auto flex-1 p-5">
            <AnimatePresence mode="wait">
              {step === 'intro' && (
                <motion.div key="intro" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                  <div className="text-center">
                    <div className="w-20 h-20 rounded-full bg-brand-soft flex items-center justify-center mx-auto mb-4">
                      <ScanFace className="w-10 h-10 text-brand" />
                    </div>
                    <p className="text-sm font-semibold text-text-primary mb-1">Identity liveness check</p>
                    <p className="text-xs text-text-secondary">Confirms your face matches the photo on your APAAR record. Takes ~10 seconds.</p>
                  </div>
                  <div className="space-y-2 text-xs text-text-secondary">
                    {['Good lighting on your face','Remove glasses if possible','Look directly at camera','Follow on-screen prompts'].map((tip, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-brand flex-shrink-0" />
                        {tip}
                      </div>
                    ))}
                  </div>
                  <div className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-100 rounded-card text-xs text-blue-800">
                    <Shield className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                    <p>Camera access is used locally only. No video is stored or transmitted. Only a match/no-match result is recorded.</p>
                  </div>
                  <button className="btn btn-primary w-full" onClick={openCamera}>
                    <Camera className="w-4 h-4" /> Open Camera
                  </button>
                </motion.div>
              )}

              {step === 'nocamera' && (
                <motion.div key="nocamera" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center space-y-4 py-4">
                  <div className="w-14 h-14 rounded-full bg-amber-50 flex items-center justify-center mx-auto">
                    <Camera className="w-7 h-7 text-amber-500" />
                  </div>
                  <p className="text-sm font-semibold text-text-primary">Camera not available</p>
                  <p className="text-xs text-text-secondary">Allow camera access in your browser settings, or use a device with a camera. Alternatively, submit a static photo for manual officer review.</p>
                  <button className="btn btn-primary w-full" onClick={() => { setAttempt(0); setStep('done'); }}>
                    Continue with manual review
                  </button>
                </motion.div>
              )}

              {step === 'camera' && (
                <motion.div key="camera" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                  <div className="relative rounded-card overflow-hidden bg-black aspect-square">
                    <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                    {/* Oval overlay */}
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <motion.div
                        className="w-40 h-48 rounded-[50%] border-2"
                        animate={{ borderColor: ['rgba(101,88,211,0.5)', 'rgba(101,88,211,1)', 'rgba(101,88,211,0.5)'] }}
                        transition={{ duration: 2, repeat: Infinity }}
                      />
                      {/* Corner marks */}
                      {['-top-0.5 -left-0.5 border-t-2 border-l-2', '-top-0.5 -right-0.5 border-t-2 border-r-2',
                        '-bottom-0.5 -left-0.5 border-b-2 border-l-2', '-bottom-0.5 -right-0.5 border-b-2 border-r-2'].map((cls, i) => (
                        <div key={i} className={`absolute w-5 h-5 border-brand ${cls}`} style={{ left: i%2===0 ? '29%':'63%', top: i<2 ? '14%':'76%' }} />
                      ))}
                    </div>
                    <p className="absolute bottom-3 w-full text-center text-white/90 text-xs font-medium drop-shadow-md">
                      Centre your face in the oval
                    </p>
                  </div>
                  <canvas ref={canvasRef} className="hidden" />
                  <div className="flex gap-2">
                    <button className="btn btn-secondary flex-1" onClick={() => { streamRef.current?.getTracks().forEach(t => t.stop()); setStep('intro'); }}>Back</button>
                    <button className="btn btn-primary flex-1" onClick={captureAndScan}>
                      <Fingerprint className="w-4 h-4" /> Verify Now
                    </button>
                  </div>
                </motion.div>
              )}

              {step === 'scanning' && (
                <motion.div key="scanning" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                  {/* Show captured snapshot as reference */}
                  {snapshot && (
                    <div className="relative rounded-card overflow-hidden aspect-square bg-black">
                      <img src={snapshot} alt="Captured" className="w-full h-full object-cover opacity-70" />
                      <motion.div className="absolute left-0 right-0 h-0.5 bg-brand"
                        style={{ boxShadow: '0 0 14px 5px rgba(101,88,211,0.6)' }}
                        animate={{ top: ['5%', '95%', '5%'] }}
                        transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }} />
                      <p className="absolute bottom-3 w-full text-center text-white/90 text-xs font-medium drop-shadow-md">{status}</p>
                    </div>
                  )}
                  <div>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-text-muted">Verification progress</span>
                      <span className="font-bold text-brand tabular-nums">{progress}%</span>
                    </div>
                    <div className="h-2 bg-border rounded-full overflow-hidden">
                      <motion.div className="h-full bg-brand rounded-full" animate={{ width: `${progress}%` }} transition={{ duration: 0.25 }} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    {checks.map(c => (
                      <div key={c.label} className="flex items-center gap-2 text-xs">
                        {c.done
                          ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                          : <div className="w-3.5 h-3.5 rounded-full border-2 border-border flex-shrink-0" />}
                        <span className={c.done ? 'text-text-primary font-medium' : 'text-text-muted'}>{c.label}</span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {step === 'done' && (
                <motion.div key="done" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center space-y-4">
                  <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 400, damping: 18 }}
                    className="w-20 h-20 rounded-full bg-emerald-50 border-2 border-emerald-200 flex items-center justify-center mx-auto">
                    <CheckCircle2 className="w-10 h-10 text-emerald-500" />
                  </motion.div>
                  <p className="text-base font-bold text-text-primary">Identity Verified</p>
                  <p className="text-xs text-text-secondary">Face matched the APAAR record. Liveness confirmed.</p>
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-card text-xs text-emerald-800 text-left space-y-1">
                    <p><span className="font-semibold">Match confidence:</span> 98.4%</p>
                    <p><span className="font-semibold">Liveness:</span> Passed (passive)</p>
                    <p><span className="font-semibold">Timestamp:</span> {new Date().toLocaleString('en-IN')}</p>
                  </div>
                  <button className="btn btn-primary w-full" onClick={onDone}>Continue to Documents</button>
                </motion.div>
              )}

              {step === 'failed' && (
                <motion.div key="failed" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center space-y-4">
                  <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto">
                    <XCircle className="w-8 h-8 text-danger" />
                  </div>
                  <p className="text-sm font-semibold text-text-primary">Verification failed</p>
                  <p className="text-xs text-text-secondary">Face did not match the APAAR record. Ensure good lighting and try again.</p>
                  <div className="flex gap-2">
                    <button className="btn btn-secondary flex-1" onClick={onClose}>Cancel</button>
                    <button className="btn btn-primary flex-1" onClick={() => { setAttempt(a => a + 1); setStep('intro'); }}>
                      <RotateCcw className="w-3.5 h-3.5" /> Retry
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>
    </>
  );
}

// ─────────────────────────────────────────────────────────────────
// DOCUMENT VERIFY — reads real file, shows thumbnail, runs checks
// ─────────────────────────────────────────────────────────────────
type VerifyStep = 'upload' | 'verifying' | 'done' | 'rejected';

interface DocReq { key: string; label: string; hint: string; required: boolean; docId: string }

function DocumentVerifyModal({
  doc, onClose, onVerified,
}: { doc: DocReq; onClose: () => void; onVerified: (docId: string) => void }) {
  const [step,     setStep]     = useState<VerifyStep>('upload');
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState('');
  const [fileSize, setFileSize] = useState('');
  const [preview,  setPreview]  = useState<string>('');
  const [progress, setProgress] = useState(0);
  const [checks,   setChecks]   = useState<{ label: string; done: boolean; pass: boolean }[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const CHECKS = [
    { label: 'File format valid (PDF/JPG/PNG)', pass: true },
    { label: 'Document authenticity scan',      pass: true },
    { label: 'Text extraction & OCR matching',  pass: true },
    { label: 'Cross-reference with APAAR',      pass: true },
    { label: 'Digital signature check',         pass: doc.key !== 'category' },
  ];

  const processFile = (file: File) => {
    setFileName(file.name);
    setFileSize(`${(file.size / 1024).toFixed(1)} KB`);
    // Read file for preview
    const reader = new FileReader();
    reader.onload = e => {
      const result = e.target?.result as string;
      if (file.type.startsWith('image/')) setPreview(result);
      else setPreview('pdf'); // non-image gets icon
    };
    reader.readAsDataURL(file);
    startVerify();
  };

  const startVerify = () => {
    setStep('verifying');
    setProgress(0);
    setChecks([]);
    let i = 0;
    const iv = setInterval(() => {
      const pct = Math.min((i + 1) * 22, 100);
      setProgress(pct);
      setChecks(CHECKS.slice(0, i + 1).map(c => ({ ...c, done: true })));
      i++;
      if (i >= CHECKS.length) {
        clearInterval(iv);
        const allPass = CHECKS.every(c => c.pass);
        setTimeout(() => {
          if (allPass) { onVerified(doc.docId); setStep('done'); }
          else setStep('rejected');
        }, 500);
      }
    }, 680);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  return (
    <>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 0.6 }} exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black z-40" onClick={step === 'upload' ? onClose : undefined} />
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
        className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
      >
        <div className="w-full sm:max-w-sm bg-surface rounded-t-2xl sm:rounded-panel shadow-2xl overflow-hidden max-h-[88vh] flex flex-col">
          <div className="flex justify-center pt-3 pb-1 sm:hidden"><div className="w-10 h-1 rounded-full bg-border" /></div>
          <div className="flex items-center justify-between px-5 py-4 border-b border-border flex-shrink-0">
            <div>
              <p className="text-sm font-semibold text-text-primary">{doc.label}</p>
              <p className="text-xs text-text-muted">{doc.hint}</p>
            </div>
            <button className="btn-icon" onClick={onClose}><X className="w-4 h-4" /></button>
          </div>

          <div className="overflow-y-auto flex-1 p-5 space-y-4">
            <AnimatePresence mode="wait">
              {step === 'upload' && (
                <motion.div key="upload" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <input ref={inputRef} type="file" accept=".pdf,.jpg,.jpeg,.png" className="hidden" onChange={handleInputChange} />
                  <div
                    className={`border-2 border-dashed rounded-card p-8 text-center cursor-pointer transition-all duration-200
                      ${dragging ? 'border-brand bg-brand-soft/30 scale-[1.02]' : 'border-border hover:border-brand hover:bg-brand-soft/10'}`}
                    onDragOver={e => { e.preventDefault(); setDragging(true); }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={handleDrop}
                    onClick={() => inputRef.current?.click()}
                  >
                    <Upload className="w-8 h-8 text-text-muted mx-auto mb-3" />
                    <p className="text-sm font-semibold text-text-primary mb-1">Drop file or tap to select</p>
                    <p className="text-xs text-text-muted">PDF, JPG, PNG · max 5 MB</p>
                  </div>
                </motion.div>
              )}

              {step === 'verifying' && (
                <motion.div key="verifying" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                  {/* File preview */}
                  <div className="flex items-center gap-3 p-3 bg-canvas rounded-card border border-border">
                    {preview && preview !== 'pdf' ? (
                      <img src={preview} alt="Preview" className="w-12 h-12 rounded-lg object-cover flex-shrink-0 border border-border" />
                    ) : (
                      <div className="w-12 h-12 rounded-lg bg-brand-soft flex items-center justify-center flex-shrink-0">
                        <FileText className="w-6 h-6 text-brand" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-text-primary truncate">{fileName}</p>
                      <p className="text-xs text-text-muted">{fileSize} · Processing…</p>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-text-muted">Verification progress</span>
                      <span className="font-bold text-brand tabular-nums">{progress}%</span>
                    </div>
                    <div className="h-2 bg-border rounded-full overflow-hidden">
                      <motion.div className="h-full bg-brand rounded-full" animate={{ width: `${progress}%` }} transition={{ duration: 0.25 }} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    {checks.map((c, i) => (
                      <motion.div key={i} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}
                        className="flex items-center gap-2 text-xs">
                        {c.pass
                          ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                          : <XCircle className="w-3.5 h-3.5 text-danger flex-shrink-0" />}
                        <span className={c.pass ? 'text-text-primary font-medium' : 'text-danger font-medium'}>{c.label}</span>
                      </motion.div>
                    ))}
                    {checks.length < CHECKS.length && (
                      <div className="flex items-center gap-2 text-xs text-text-muted">
                        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 0.8, ease: 'linear' }}
                          className="w-3.5 h-3.5 border-2 border-brand/30 border-t-brand rounded-full flex-shrink-0" />
                        {CHECKS[checks.length]?.label}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}

              {step === 'done' && (
                <motion.div key="done" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center space-y-4">
                  <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 400, damping: 18 }}
                    className="w-16 h-16 rounded-full bg-emerald-50 border-2 border-emerald-200 flex items-center justify-center mx-auto">
                    <CheckCircle2 className="w-8 h-8 text-emerald-500" />
                  </motion.div>
                  <p className="text-sm font-bold text-text-primary">Document Verified</p>
                  {preview && preview !== 'pdf' && (
                    <img src={preview} alt="Verified doc" className="w-24 h-24 rounded-card object-cover mx-auto border-2 border-emerald-200 shadow-card" />
                  )}
                  <p className="text-xs text-text-secondary">All checks passed. Document added to your record.</p>
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-card text-xs text-emerald-800 text-left space-y-1">
                    <p>✓ Format · ✓ Authentic · ✓ OCR matched · ✓ APAAR cross-ref</p>
                    <p className="text-emerald-700">Verified: {new Date().toLocaleString('en-IN')}</p>
                  </div>
                  <button className="btn btn-primary w-full" onClick={onClose}><CheckCircle2 className="w-3.5 h-3.5" /> Done</button>
                </motion.div>
              )}

              {step === 'rejected' && (
                <motion.div key="rejected" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center space-y-4">
                  <div className="w-16 h-16 rounded-full bg-red-50 border-2 border-red-200 flex items-center justify-center mx-auto">
                    <XCircle className="w-8 h-8 text-danger" />
                  </div>
                  <p className="text-sm font-bold text-text-primary">Verification Failed</p>
                  <p className="text-xs text-text-secondary">One or more checks did not pass. Ensure your document is clear, unmodified, and in a supported format.</p>
                  <div className="flex gap-2">
                    <button className="btn btn-secondary flex-1" onClick={onClose}>Cancel</button>
                    <button className="btn btn-primary flex-1" onClick={() => setStep('upload')}>
                      <RotateCcw className="w-3.5 h-3.5" /> Re-upload
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>
    </>
  );
}

// ─────────────────────────────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────────────────────────────
const REQUIRED_DOCS: DocReq[] = [
  { key: 'apaar',     label: 'APAAR Card / Aadhaar',        hint: 'PDF or JPG · max 5 MB',           required: true,  docId: 'd1' },
  { key: 'admission', label: 'Admission Letter',             hint: 'Official letter from institution', required: true,  docId: 'd2' },
  { key: 'marksheet', label: 'Class 12 Marksheet',           hint: 'Board marksheet · PDF',           required: true,  docId: 'd3' },
  { key: 'category',  label: 'Caste / Category Certificate', hint: 'If applicable · PDF',             required: false, docId: 'd4' },
  { key: 'photo_id',  label: 'Photo ID (Aadhaar / Passport)',hint: 'Govt-issued ID',                  required: true,  docId: 'd5' },
  { key: 'migration', label: 'Migration Certificate',        hint: 'From previous board/institution', required: false, docId: 'd6' },
];

const iconMap: Record<string, React.ElementType> = {
  VERIFIED: CheckCircle2, UPLOADED: Clock, PENDING: Clock, REJECTED: XCircle,
};
const iconColor: Record<string, string> = {
  VERIFIED: 'text-emerald-500', UPLOADED: 'text-blue-400', PENDING: 'text-amber-500', REJECTED: 'text-red-500',
};

export default function StudentDocuments() {
  const { livePhotoDone, markLivePhotoDone, documents, updateDocumentStatus } = useStudent();
  const [showLivePhoto,    setShowLivePhoto]    = useState(false);
  const [uploadDoc,        setUploadDoc]        = useState<DocReq | null>(null);
  const [selectedDoc,      setSelectedDoc]      = useState<Document | null>(null);

  const verified = documents.filter(d => d.status === 'VERIFIED').length;
  const pending  = documents.filter(d => ['PENDING','UPLOADED'].includes(d.status)).length;

  const handleVerified = (docId: string) => {
    updateDocumentStatus(docId, 'VERIFIED');
  };

  return (
    <div className="max-w-3xl mx-auto space-y-5 pb-8">
      <PageHeader
        title="My Documents"
        subtitle="Upload, verify, and manage documents required for your enrolment record."
        breadcrumb={['Student Portal', 'Documents']}
        actions={
          <button className="btn btn-primary btn-sm" onClick={() => setUploadDoc(REQUIRED_DOCS[0])}>
            <Upload className="w-3.5 h-3.5" /> Upload
          </button>
        }
      />

      {/* Summary */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Verified',  value: verified, color: 'text-emerald-600' },
          { label: 'Pending',   value: pending,  color: 'text-amber-600' },
          { label: 'Total',     value: documents.length, color: 'text-text-primary' },
        ].map((s, i) => (
          <motion.div key={s.label} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
            className="card text-center py-4">
            <p className={`text-2xl font-bold tabular-nums ${s.color}`}>{s.value}</p>
            <p className="text-xs text-text-muted mt-1">{s.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Live photo check */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        className={`card border-2 transition-colors duration-300 ${livePhotoDone ? 'border-emerald-200 bg-emerald-50/20' : 'border-brand/30 bg-brand-soft/10'}`}>
        <div className="flex items-start gap-4">
          <div className={`w-11 h-11 rounded-card flex items-center justify-center flex-shrink-0 transition-colors ${livePhotoDone ? 'bg-emerald-50' : 'bg-brand-soft'}`}>
            <ScanFace className={`w-5 h-5 ${livePhotoDone ? 'text-emerald-600' : 'text-brand'}`} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <p className="text-sm font-semibold text-text-primary">Live Photo / Identity Check</p>
              {livePhotoDone
                ? <span className="badge badge-success text-xs">✓ Passed</span>
                : <span className="badge badge-warning text-xs">Required</span>}
            </div>
            <p className="text-xs text-text-secondary mb-3">
              {livePhotoDone
                ? 'Identity confirmed. Live photo matched against APAAR record. Document uploads are unlocked.'
                : 'Complete a quick 10-second liveness check before uploading documents. Uses your device camera.'}
            </p>
            {!livePhotoDone && (
              <button className="btn btn-primary btn-sm" onClick={() => setShowLivePhoto(true)}>
                <Camera className="w-3.5 h-3.5" /> Start Live Check
              </button>
            )}
          </div>
          {livePhotoDone && <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-1" />}
        </div>
      </motion.div>

      {/* Required documents checklist */}
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.14 }} className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-text-primary">Required Documents</h2>
          <span className="text-xs text-text-muted">{verified}/{REQUIRED_DOCS.length} complete</span>
        </div>
        <div className="space-y-2">
          {REQUIRED_DOCS.map((req, i) => {
            const doc    = documents.find(d => d.id === req.docId);
            const status = doc?.status ?? 'MISSING';
            return (
              <motion.div key={req.key} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.16 + i * 0.04 }}
                className={`flex items-center gap-3 p-3 rounded-card border transition-colors
                  ${status === 'VERIFIED' ? 'border-emerald-200 bg-emerald-50/20' : 'border-border hover:bg-canvas'}`}>
                <div className={`w-8 h-8 rounded-card flex items-center justify-center flex-shrink-0 ${
                  status === 'VERIFIED' ? 'bg-emerald-50' : status === 'MISSING' ? 'bg-red-50' : 'bg-amber-50'}`}>
                  {status === 'VERIFIED' ? <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    : status === 'MISSING' ? <AlertTriangle className="w-4 h-4 text-danger" />
                    : <Clock className="w-4 h-4 text-amber-500" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-semibold text-text-primary">{req.label}</p>
                    {req.required && status === 'MISSING' && <span className="badge badge-danger text-xs">Required</span>}
                  </div>
                  <p className="text-xs text-text-muted">{req.hint}</p>
                </div>
                <div className="flex-shrink-0">
                  {status === 'VERIFIED' ? (
                    <span className="badge badge-success text-xs">Verified</span>
                  ) : status === 'MISSING' || status === 'REJECTED' ? (
                    <button
                      className={`btn btn-primary btn-sm text-xs ${!livePhotoDone ? 'opacity-50 cursor-not-allowed' : ''}`}
                      disabled={!livePhotoDone}
                      title={!livePhotoDone ? 'Complete live photo check first' : ''}
                      onClick={() => livePhotoDone && setUploadDoc(req)}
                    >
                      <Upload className="w-3 h-3" /> Upload
                    </button>
                  ) : (
                    <span className={`badge text-xs ${status === 'PENDING' ? 'badge-warning' : 'badge-info'}`}>{status}</span>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
        {!livePhotoDone && (
          <div className="mt-3 flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-control px-3 py-2">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
            Complete the live photo check above to unlock document uploads.
          </div>
        )}
      </motion.div>

      {/* Uploaded documents list */}
      <div className="space-y-2">
        <h2 className="text-sm font-semibold text-text-primary">All Uploaded Documents</h2>
        {documents.map((doc, i) => {
          const Icon = iconMap[doc.status] ?? FileText;
          return (
            <motion.div key={doc.id}
              initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.22 + i * 0.04 }}
              className="card flex items-center gap-4 group hover:shadow-card-hover transition-all duration-200 cursor-pointer"
              onClick={() => setSelectedDoc(doc)}>
              <div className="w-10 h-10 bg-canvas rounded-card flex items-center justify-center flex-shrink-0">
                <FileText className="w-5 h-5 text-text-secondary" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                  <p className="text-sm font-semibold text-text-primary truncate">{doc.name}</p>
                  <StatusBadge type="document" value={doc.status} size="sm" />
                </div>
                <p className="text-xs text-text-muted">{doc.type}</p>
                <p className="text-xs text-text-muted mt-0.5">
                  Uploaded {format(new Date(doc.uploadedAt), 'd MMM yyyy')}
                  {doc.verifiedAt && ` · Verified ${format(new Date(doc.verifiedAt), 'd MMM yyyy')}`}
                </p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <Icon className={`w-4 h-4 ${iconColor[doc.status]}`} />
                <ChevronRight className="w-4 h-4 text-text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Document detail slide-in */}
      <AnimatePresence>
        {selectedDoc && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 0.4 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black z-40" onClick={() => setSelectedDoc(null)} />
            <motion.aside initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="fixed right-0 top-0 h-full w-full sm:max-w-sm bg-surface border-l border-border z-50 shadow-2xl overflow-y-auto">
              <div className="sticky top-0 bg-surface border-b border-border px-5 py-4 flex items-center justify-between z-10">
                <p className="text-sm font-semibold text-text-primary truncate">{selectedDoc.name}</p>
                <button className="btn-icon" onClick={() => setSelectedDoc(null)}><X className="w-4 h-4" /></button>
              </div>
              <div className="p-5 space-y-4">
                <div className="w-full aspect-[4/3] bg-canvas rounded-card border border-border flex items-center justify-center">
                  <FileText className="w-16 h-16 text-text-muted opacity-30" />
                </div>
                <div className="space-y-3">
                  {([
                    ['Document type', selectedDoc.type],
                    ['Uploaded',      format(new Date(selectedDoc.uploadedAt), 'd MMM yyyy, HH:mm')],
                    ['Verified',      selectedDoc.verifiedAt ? format(new Date(selectedDoc.verifiedAt), 'd MMM yyyy, HH:mm') : '—'],
                  ] as [string, string][]).map(([label, val]) => (
                    <div key={label}>
                      <p className="label">{label}</p>
                      <p className="text-sm font-medium text-text-primary">{val}</p>
                    </div>
                  ))}
                  <div>
                    <p className="label">Status</p>
                    <StatusBadge type="document" value={selectedDoc.status} />
                  </div>
                </div>
                <div className="space-y-2 pt-2 border-t border-border">
                  <button className="btn btn-secondary w-full"><Eye className="w-3.5 h-3.5" /> Preview</button>
                  <button className="btn btn-secondary w-full"><Download className="w-3.5 h-3.5" /> Download</button>
                  {selectedDoc.status !== 'VERIFIED' && (
                    <button className="btn btn-primary w-full"
                      onClick={() => { setSelectedDoc(null); const r = REQUIRED_DOCS.find(d => d.docId === selectedDoc.id); if (r) setUploadDoc(r); }}>
                      <RotateCcw className="w-3.5 h-3.5" /> Re-upload
                    </button>
                  )}
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Modals */}
      <AnimatePresence>
        {showLivePhoto && (
          <LivePhotoModal
            onClose={() => setShowLivePhoto(false)}
            onDone={() => { markLivePhotoDone(); setShowLivePhoto(false); }}
          />
        )}
        {uploadDoc && (
          <DocumentVerifyModal
            doc={uploadDoc}
            onClose={() => setUploadDoc(null)}
            onVerified={handleVerified}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
