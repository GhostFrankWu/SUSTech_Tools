import javax.swing.*;
import java.awt.*;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;

public class Layer extends JFrame {
    public Layer() {
        Dimension sc = Toolkit.getDefaultToolkit().getScreenSize();
        setSize(sc.width, sc.height);
        setLocation(0, 0);
        setUndecorated(true);        //窗口去边框
        setAlwaysOnTop(true);        //设置窗口总在最前
        setBackground(new Color(0, 0, 0, 0));
        addMouseListener(new MouseAdapter() {
            public void mousePressed(MouseEvent e) {
                try{
                    Runtime.getRuntime().exec("rundll32.exe user32.dll,LockWorkStation");
                }catch (Exception ignored){}
                System.exit(0);
            }
        });
    }
}
