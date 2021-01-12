import javax.imageio.ImageIO;
import javax.swing.*;
import javax.swing.text.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Vector;

public class Screen extends JFrame {
    private static Layer dark;
    private static final int Times = 5;
    public static Art bg1 = new Art();
    public static String bg1s, bg2s;
    private static JLabel texts = new JLabel();
    private static Vector<JTextPane> pool = new Vector<>();
    public static BufferedImage background1, background2;
    private static ArrayList<String> data = new ArrayList<>();
    private static File[] files = new File("bg\\").listFiles();
    private static boolean flagForChange = false;
    public static int width = 1920, height = 1080;
    private MutableAttributeSet attrSet = new SimpleAttributeSet();
    private static Font font;

    private void load() {
        try {
            InputStreamReader reader = new InputStreamReader(new FileInputStream(new File("res\\data.txt")), StandardCharsets.UTF_8);
            BufferedReader br = new BufferedReader(reader);
            String line = br.readLine();
            while (line != null) {
                data.add(line.trim());
                line = br.readLine();
            }
        } catch (IOException ignored) {
        }
        bg1s = files[(int) (Math.random() * files.length)].getPath();
        bg2s = files[(int) (Math.random() * files.length)].getPath();
        while (bg1s.equals(bg2s)) {
            bg2s = files[(int) (Math.random() * files.length)].getPath();
        }
        setBackground(bg1s, true);
        setBackground(bg2s, false);
        for (int i = 0; i < Times; i++) {
            insert();
        }
    }

    private static void setBackground(String name, boolean flag) {
        try {
            BufferedImage orin_img = (ImageIO.read(new File(name)));
            BufferedImage newImage = new BufferedImage(width, height, orin_img.getType());
            Graphics g = newImage.getGraphics();
            g.drawImage(orin_img, 0, 0, width, height, null);
            g.dispose();
            orin_img = newImage;
            if (flag) {
                background1 = orin_img;
                bg1.setIcon(new ImageIcon(background1));
            } else {
                background2 = orin_img;
            }
        } catch (IOException ignored) {
        }
    }

    public class realChange extends Thread {
        public void run() {
            background1 = background2;
            bg1.setIcon(new ImageIcon(background1));
            bg1s = bg2s;
            while (bg1s.equals(bg2s)) {
                bg2s = files[(int) (Math.random() * files.length)].getPath();
            }
            setBackground(bg2s, false);
            new flush().start();
        }
    }

    public class flush extends Thread {
        public void run() {
            setVisible(true);
            try {
                for (int i = 255; i > 0; i -= 1) {
                    dark.setBackground(new Color(0, 0, 0, i));
                    Thread.sleep(4);
                    dark.repaint();
                }
                flagForChange = false;
            } catch (Exception ignored) {
            }
            System.gc();
        }
    }

    public void insert() {
        JTextPane jt = new JTextPane();
        jt.setLocation((int) (Math.random() * width / 4),
                (int) (Math.random() * (height-100) / 100 + (height-100) * Math.random())
        );
        jt.setSize(width - jt.getX(), height - jt.getY());
        jt.setFont(font);
        StyleConstants.setForeground(attrSet, new Color((int) (Math.random() * 205) + 50, (int) (Math.random() * 205) + 50,
                (int) (Math.random() * 205 + 50), (int) (Math.random() * 150) + 100));             //颜色
        StyleConstants.setBold(attrSet, true);
        StyleConstants.setFontSize(attrSet, (int) (Math.random() * 50) + 20);             //字体大小
        StyledDocument doc = jt.getStyledDocument();
        try {
            doc.insertString(doc.getLength(), data.get((int) (Math.random() * data.size())), attrSet);
        } catch (BadLocationException ignored) {
        }
        jt.setBackground(new Color(0, 0, 0, 0));
        jt.addMouseListener(new MouseAdapter() {
            public void mousePressed(MouseEvent e) {
                try{
                    Runtime.getRuntime().exec("rundll32.exe user32.dll,LockWorkStation");
                }catch (Exception ignored){}
                System.exit(0);
            }
        });
        texts.add(jt);
        pool.add(jt);
    }

    public class changeBackground extends Thread {
        public void run() {
            Timer changer0 = new Timer(1000, e -> {
                if (!flagForChange) {
                    if ((int) (Math.random() * 8) > 3) {
                        insert();
                    }
                    if (pool.size() > 0 && (int) (Math.random() * 8) > 5) {
                        pool.get(0).setVisible(false);
                        pool.remove(0);
                    }
                    if(pool.size()> Times*4){
                        for(int i=0;i<Times*3;i++){
                            pool.get(0).setVisible(false);
                            pool.remove(0);
                        }
                    }
                    if (texts.getComponents().length >  150) {
                        remove(texts);
                        pool.clear();
                        repaint();
                        remove(bg1);
                        texts = new JLabel();
                        texts.setLayout(null);
                        texts.setBounds(0, 0, width, height);
                        texts.setFocusable(false);
                        texts.setOpaque(false);
                        add(texts);
                        add(bg1);
                        for (int i = 0; i < Times; i++) {
                            insert();
                        }
                    }
                }
            });
            changer0.start();
            Timer changer = new Timer(25000, e -> {
                if (!flagForChange) {
                    if ((int) (Math.random() * 8) > 5) {
                        try {
                            flagForChange = true;
                            for (int i = 0; i < 255; i += 1) {
                                dark.setBackground(new Color(0, 0, 0, i));
                                Thread.sleep(4);
                                dark.repaint();
                            }
                            setVisible(false);
                            new realChange().run();
                        } catch (Exception ignored) {
                        }
                    }
                }
            });
            changer.start();
        }
    }


    public static void main(String[] args) {
        new Screen();
        dark = new Layer();
        dark.setVisible(true);
    }

    private Image offScreenImage = null;

    public void update(Graphics g) {
        if (offScreenImage == null) {
            offScreenImage = this.createImage(width, height);
        }
        Graphics gOff = offScreenImage.getGraphics();
        paint(gOff);
        g.drawImage(offScreenImage, 1, 0, null);
    }

    public Screen() {
        Dimension sc = Toolkit.getDefaultToolkit().getScreenSize();
        try {
            font = Font.createFont(Font.TRUETYPE_FONT, new BufferedInputStream(new FileInputStream(new File("res\\normal.ttf"))));
            font = font.deriveFont(Font.PLAIN, 30);
        } catch (Exception ignored) {
        }
        width = sc.width;
        height = sc.height;
        setSize(width, height);
        setLocation(0, 0);
        setUndecorated(true);
        setBackground(new Color(0, 0, 0, 0));
        addMouseListener(new MouseAdapter() {
            public void mousePressed(MouseEvent e) {
                try{
                    Runtime.getRuntime().exec("rundll32.exe user32.dll,LockWorkStation");
                }catch (Exception ignored){}
                System.exit(0);
            }
        });
        bg1.setSize(width, height);
        bg1.setLocation(0, 0);
        bg1.setBackground(Color.BLACK);
        load();
        new changeBackground().start();
        texts.setLayout(null);
        texts.setBounds(0, 0, width, height);
        texts.setFocusable(false);
        texts.setOpaque(false);
        add(texts);
        add(bg1);
        setVisible(true);
    }
}
