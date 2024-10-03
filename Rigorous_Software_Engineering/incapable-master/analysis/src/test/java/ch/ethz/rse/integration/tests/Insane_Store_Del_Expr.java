
package ch.ethz.rse.integration.tests;

import ch.ethz.rse.Store;

// expected results:
// NON_NEGATIVE SAFE
// FITS_IN_TROLLEY UNSAFE
// FITS_IN_RESERVE SAFE

public class Insane_Store_Del_Expr {
  public static void m1(int j){
    Store s = new Store(3, 1000);
    

    s.get_delivery(4 * 4 + 12 + 48 * 4);
    
   }
 }

