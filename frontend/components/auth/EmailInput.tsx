"use client";

interface EmailInputProps {
  email: string;
  onChange: (next: string) => void;
  disabled?: boolean;
}

export default function EmailInput({ email, onChange, disabled = false }: EmailInputProps) {
  return (
    <div className="mb-4">
      <input
        type="email"
        placeholder="you@example.com"
        value={email}
        onChange={(e) => onChange(e.target.value.trim())}
        className="input-field"
        autoFocus
        disabled={disabled}
        id="email-input"
      />
    </div>
  );
}
