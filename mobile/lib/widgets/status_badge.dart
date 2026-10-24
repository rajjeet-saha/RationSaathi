import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';

enum BadgeType { verified, unverified, blocked, pending, overdue }

class StatusBadge extends StatelessWidget {
  final String label;
  final BadgeType type;

  const StatusBadge({
    super.key,
    required this.label,
    required this.type,
  });

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    IconData icon;

    switch (type) {
      case BadgeType.verified:
        bg = AppTheme.verifiedGreen.withOpacity(0.12);
        fg = AppTheme.verifiedGreen;
        icon = Icons.verified_user_outlined;
        break;
      case BadgeType.unverified:
        bg = Colors.grey.withOpacity(0.15);
        fg = Colors.black87;
        icon = Icons.help_outline;
        break;
      case BadgeType.blocked:
        bg = AppTheme.blockedRed.withOpacity(0.12);
        fg = AppTheme.blockedRed;
        icon = Icons.block;
        break;
      case BadgeType.pending:
        bg = AppTheme.pendingAmber.withOpacity(0.12);
        fg = AppTheme.pendingAmber;
        icon = Icons.hourglass_top_outlined;
        break;
      case BadgeType.overdue:
        bg = AppTheme.blockedRed.withOpacity(0.15);
        fg = AppTheme.blockedRed;
        icon = Icons.warning_amber_rounded;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: fg.withOpacity(0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: fg),
          const SizedBox(width: 5),
          Text(
            label,
            style: TextStyle(
              color: fg,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
