import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { Resend } from 'resend';
import NodeCache from 'node-cache';
import mongoose from 'mongoose';
import bcrypt from 'bcryptjs';
import path from 'path';
import { fileURLToPath } from 'url';

// Resolve directory path for ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load .env from two folders up (waSaa\.env)
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const app = express();
app.use(cors());
app.use(express.json());

// ----------------------------------------------------
// 1. MONGODB CONNECTION & USER SCHEMA
// ----------------------------------------------------
const MONGODB_URI = process.env.MONGODB_URI;

if (!MONGODB_URI) {
  console.error('❌ MONGODB_URI is missing from waSaa\\.env!');
} else {
  mongoose
    .connect(MONGODB_URI)
    .then(() => console.log('🍃 Connected to MongoDB successfully!'))
    .catch((err) => console.error('❌ MongoDB Connection Error:', err));
}

const userSchema = new mongoose.Schema(
  {
    name: { type: String, required: false },
    email: { type: String, required: true, unique: true, lowercase: true, trim: true },
    phone: { type: String, required: false },
    password: { type: String, required: true },
    isVerified: { type: Boolean, default: true },
  },
  { timestamps: true }
);

const User = mongoose.model('User', userSchema);

// ----------------------------------------------------
// 2. RESEND & CACHE INITIALIZATION
// ----------------------------------------------------
const resendKey = process.env.RESEND_API_KEY;
if (!resendKey) {
  console.warn('⚠️ WARNING: RESEND_API_KEY is not defined in waSaa\\.env');
}

const resend = new Resend(resendKey || 'dummy_key');
const otpCache = new NodeCache({ stdTTL: 300 }); // 5 minutes TTL

// ----------------------------------------------------
// 3. API ROUTES
// ----------------------------------------------------

/**
 * REQUEST OTP
 */
app.post('/api/auth/request-otp', async (req, res) => {
  const { email } = req.body;

  if (!email) {
    return res.status(400).json({ message: 'Email is required.' });
  }

  const normalizedEmail = email.trim().toLowerCase();

  try {
    // Check if user already exists in MongoDB
    const existingUser = await User.findOne({ email: normalizedEmail });
    if (existingUser) {
      return res.status(400).json({ message: 'An account with this email already exists.' });
    }

    // Generate 6-digit numeric OTP
    const otp = Math.floor(100000 + Math.random() * 900000).toString();

    // Store in cache
    otpCache.set(normalizedEmail, otp);

    console.log(`\n========================================`);
    console.log(`[LOCAL DEV] OTP Generated for ${normalizedEmail}: ${otp}`);
    console.log(`========================================\n`);

    const { data, error } = await resend.emails.send({
      from: 'onboarding@resend.dev',
      to: [normalizedEmail],
      subject: 'Your Registration Verification Code',
      html: `
        <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 500px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px;">
          <h2 style="color: #333;">Verify your account</h2>
          <p style="color: #666;">Your 6-digit verification code is:</p>
          <div style="letter-spacing: 6px; font-size: 32px; font-weight: bold; color: #4F46E5; background-color: #f4f4f5; padding: 16px; text-align: center; border-radius: 6px; margin: 20px 0;">
            ${otp}
          </div>
          <p style="color: #888; font-size: 13px;">This code will expire in 5 minutes.</p>
        </div>
      `,
    });

    if (error) {
      console.error('Resend Delivery Note:', error.message);
      return res.status(200).json({
        message: 'OTP processed! Check your terminal console for the code.',
        devNote: error.message,
      });
    }

    return res.status(200).json({ message: 'OTP sent to your email successfully!' });

  } catch (err) {
    console.error('Server Error:', err);
    return res.status(500).json({ message: 'Internal server error.' });
  }
});

/**
 * VERIFY OTP & SAVE USER TO MONGODB
 */
app.post('/api/auth/verify-otp', async (req, res) => {
  const { name, email, phone, password, otp } = req.body;

  if (!email || !otp || !password) {
    return res.status(400).json({ message: 'Email, password, and OTP code are required.' });
  }

  const normalizedEmail = email.trim().toLowerCase();
  const cachedOtp = otpCache.get(normalizedEmail);

  if (!cachedOtp) {
    return res.status(400).json({ message: 'OTP has expired or was never requested.' });
  }

  if (cachedOtp !== String(otp).trim()) {
    return res.status(400).json({ message: 'Invalid OTP code. Please try again.' });
  }

  try {
    // 1. Encrypt user password
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);

    // 2. Insert record into MongoDB Atlas
    const newUser = await User.create({
      name,
      email: normalizedEmail,
      phone,
      password: hashedPassword,
      isVerified: true,
    });

    // 3. Clear single-use OTP
    otpCache.del(normalizedEmail);

    return res.status(201).json({
      message: 'Account verified and created successfully!',
      user: { id: newUser._id, email: newUser.email, name: newUser.name },
    });
  } catch (err) {
    console.error('Registration Error:', err);
    return res.status(500).json({ message: 'Error finalizing registration in database.' });
  }
});

/**
 * LOGIN ROUTE (Queries MongoDB)
 */
app.post('/api/auth/login', async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ message: 'Email and password are required.' });
  }

  try {
    const normalizedEmail = email.trim().toLowerCase();
    const user = await User.findOne({ email: normalizedEmail });

    if (!user) {
      return res.status(400).json({ message: 'Invalid email or password.' });
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(400).json({ message: 'Invalid email or password.' });
    }

    return res.status(200).json({
      message: 'Logged in successfully!',
      user: { id: user._id, email: user.email, name: user.name },
    });
  } catch (err) {
    console.error('Login Error:', err);
    return res.status(500).json({ message: 'Internal server error.' });
  }
});

const PORT = process.env.PORT || 8000;
app.listen(PORT, () => console.log(`🚀 Backend auth server running on http://localhost:${PORT}`));

// ----------------------------------------------------
// FAVORITES SCHEMA & MODEL
// ----------------------------------------------------
const favoriteSchema = new mongoose.Schema(
  {
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
    itemId: { type: String, required: true },       // ID of the item/product/card
    title: { type: String, required: true },        // Name of the item
    image: { type: String, required: false },       // Image URL if applicable
  },
  { timestamps: true }
);

// This ensures a user can't favorite the exact same item twice
favoriteSchema.index({ userId: 1, itemId: 1 }, { unique: true });

const Favorite = mongoose.model('Favorite', favoriteSchema);

// ----------------------------------------------------
// FAVORITES API ROUTES
// ----------------------------------------------------

/**
 * SAVE OR TOGGLE A FAVORITE
 */
app.post('/api/favorites/toggle', async (req, res) => {
  const { userId, itemId, title, image } = req.body;

  if (!userId || !itemId || !title) {
    return res.status(400).json({ message: 'Missing required fields.' });
  }

  try {
    // Check if it's already favorited
    const existingFav = await Favorite.findOne({ userId, itemId });

    if (existingFav) {
      // If it exists, remove it (Unfavorite)
      await Favorite.deleteOne({ _id: existingFav._id });
      return res.status(200).json({ message: 'Removed from favorites', isFavorited: false });
    } else {
      // If it doesn't exist, create it (Favorite)
      await Favorite.create({ userId, itemId, title, image });
      return res.status(201).json({ message: 'Added to favorites', isFavorited: true });
    }
  } catch (err) {
    console.error('Favorites Error:', err);
    return res.status(500).json({ message: 'Error processing favorite.' });
  }
});

/**
 * GET ALL FAVORITES FOR A SPECIFIC USER
 */
app.get('/api/favorites/:userId', async (req, res) => {
  const { userId } = req.params;

  try {
    const userFavorites = await Favorite.find({ userId }).sort({ createdAt: -1 });
    return res.status(200).json(userFavorites);
  } catch (err) {
    console.error('Error fetching favorites:', err);
    return res.status(500).json({ message: 'Internal server error.' });
  }
});
